"""
tools/cache.py
==================
Prompt/result cache (§3.3 "Prompt Caching" cost-optimization mandate). Every
LLM call that is deterministic given its inputs (RAG context + prompt +
model tier) is cache-keyed so repeated requests — a user reopening the same
job posting, re-rendering the same CV section twice — cost zero additional
tokens.

Backed by Redis when `settings.redis_url` is reachable; transparently falls
back to an in-process dict with the same TTL semantics if Redis is down or
not configured, so the rest of the codebase never branches on which backend
is active. This mirrors the live/mock pattern used everywhere else in
app/tools/ — callers depend on `get_cache()` only.
"""

from __future__ import annotations

import hashlib
import json
import time
from abc import ABC, abstractmethod
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def make_cache_key(*parts: str) -> str:
    """
    Build a stable cache key from arbitrary string parts (e.g. agent name +
    model tier + normalized prompt text) by hashing their concatenation.
    SHA256 keeps key length constant regardless of prompt size, which
    matters once full RAG-augmented prompts (multiple KB) are part of the key.
    """
    joined = "::".join(parts)
    digest = hashlib.sha256(joined.encode("utf-8")).hexdigest()
    return f"ck:{digest}"


class BaseCache(ABC):
    @abstractmethod
    async def get(self, key: str) -> Any | None: ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...


class RedisCache(BaseCache):
    """Redis-backed cache, used when REDIS_URL is configured and reachable."""

    def __init__(self, redis_url: str) -> None:
        import redis.asyncio as redis

        self._client = redis.from_url(redis_url, decode_responses=True)

    async def get(self, key: str) -> Any | None:
        raw = await self._client.get(key)
        return json.loads(raw) if raw is not None else None

    async def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        await self._client.set(key, json.dumps(value, default=str), ex=ttl_seconds)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def ping(self) -> bool:
        return bool(await self._client.ping())


class InMemoryCache(BaseCache):
    """
    Process-local fallback cache. Not shared across worker processes and
    lost on restart — acceptable for local dev / mock mode, NOT a
    substitute for Redis in any multi-worker production deployment (this
    tradeoff is called out explicitly in the README deployment notes).
    """

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}  # key -> (expires_at, value)

    async def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    async def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        self._store[key] = (time.monotonic() + ttl_seconds, value)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)


_CACHE_SINGLETON: BaseCache | None = None


async def get_cache() -> BaseCache:
    """
    Return the process-wide cache singleton. Attempts Redis first (if
    configured); on ANY connection failure, logs a warning once and
    permanently falls back to `InMemoryCache` for the rest of the process
    lifetime rather than retrying Redis on every call (which would add
    latency to the hot path).
    """
    global _CACHE_SINGLETON
    if _CACHE_SINGLETON is not None:
        return _CACHE_SINGLETON

    if settings.redis_url:
        try:
            candidate = RedisCache(settings.redis_url)
            await candidate.ping()
            _CACHE_SINGLETON = candidate
            logger.info("cache_backend_selected", backend="redis")
            return _CACHE_SINGLETON
        except Exception as exc:  # noqa: BLE001 — any Redis failure should fall back, not crash boot
            logger.warning("cache_backend_redis_unavailable_falling_back", error=str(exc))

    _CACHE_SINGLETON = InMemoryCache()
    logger.info("cache_backend_selected", backend="in_memory")
    return _CACHE_SINGLETON


async def cached_call(key: str, ttl_seconds: int, compute: "Any") -> Any:
    """
    Cache-aside helper: return the cached value for `key` if present,
    otherwise await `compute()` (a zero-arg async callable), store its
    result, and return it. Centralizing this pattern means agents never
    hand-roll get/compute/set logic, which is what makes it safe to apply
    consistently across every LLM-calling agent per §3.3.
    """
    cache = await get_cache()
    hit = await cache.get(key)
    if hit is not None:
        logger.debug("cache_hit", key=key)
        return hit

    result = await compute()
    await cache.set(key, result, ttl_seconds=ttl_seconds)
    logger.debug("cache_miss_computed_and_stored", key=key)
    return result
