"""
tools/llm.py
================
LLM provider abstraction — the single chokepoint every agent in the system
calls through to talk to a language model.

Why this exists
----------------
Every Executor agent needs to (a) send a system+user prompt, optionally with
few-shot examples, (b) get back either free text or schema-validated JSON,
(c) optionally stream tokens to the caller, and (d) record how many tokens
it cost. Rather than scattering HTTP calls across a dozen agent files, every
agent calls `get_llm(tier)` and gets back an object with the same
`.generate()` / `.stream()` interface regardless of whether we're hitting
local Ollama or running fully offline with the deterministic mock.

Active provider
---------------
Local Ollama is the active CareerKundi LLM provider.
Gemini references, if any remain elsewhere, are legacy/deprecated.

`settings.llm_provider`:
  - ``ollama`` → `OllamaProvider` (default; local 8B model)
  - ``mock``   → `DeterministicMockProvider` (deterministic tests / offline)

`settings.llm_mode` is derived from the provider (``local`` | ``mock``) and
is **not** controlled by any cloud API key.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import random
import re
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Literal

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

ModelTier = Literal["flash", "pro"]

_JSON_INSTRUCTION = (
    "Respond only with valid JSON matching the requested schema. "
    "Do not include markdown fences."
)


@dataclass
class LLMResponse:
    """Normalized response shape returned by every provider, live or mock."""

    text: str
    prompt_tokens: int
    completion_tokens: int
    model: str
    cache_hit: bool = False
    parsed_json: Any | None = None


@dataclass
class PromptSpec:
    """
    Everything needed to issue one LLM call, built by a feature's prompt
    template (see app/prompts/) and handed to a provider unchanged. Keeping
    this as a flat dataclass (rather than passing five positional args
    around) means CostMonitorAgent, the cache layer, and both providers all
    share one contract.
    """

    system_prompt: str
    user_prompt: str
    temperature: float = 0.4
    max_output_tokens: int = 4096
    json_schema: dict | None = None  # JSON-schema the output must conform to, if any
    few_shot_examples: list[dict] = field(default_factory=list)


def _estimate_tokens(text: str) -> int:
    """
    Cheap token estimator (~4 chars/token) used in mock mode and as a
    sanity fallback when Ollama does not report usage metadata.
    """
    return max(1, len(text) // 4)


def _extract_json_object(text: str) -> Any | None:
    """Best-effort extraction of the first JSON object/array from model text."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", cleaned)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


class BaseLLMProvider(ABC):
    """Common interface implemented by Ollama and the deterministic mock."""

    model_name: str

    @abstractmethod
    async def generate(self, spec: PromptSpec) -> LLMResponse:
        """Issue one non-streaming generation call."""

    @abstractmethod
    async def stream(self, spec: PromptSpec) -> AsyncIterator[str]:
        """Issue a streaming generation call, yielding text chunks as they arrive."""


class OllamaProvider(BaseLLMProvider):
    """
    Local Ollama provider (active CareerKundi LLM path).

    Uses ``POST /api/generate`` against ``settings.ollama_base_url``.
    Local LLM output is not guaranteed correct and is never treated as
    verified truth.
    """

    def __init__(self, tier: ModelTier):
        self.tier = tier
        self.model_name = (
            settings.ollama_model_pro if tier == "pro" else settings.ollama_model_flash
        )
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.timeout = settings.ollama_request_timeout_seconds

    def _build_payload(self, spec: PromptSpec, *, stream: bool) -> dict[str, Any]:
        user_prompt = spec.user_prompt
        system_prompt = spec.system_prompt
        if spec.json_schema:
            user_prompt = f"{user_prompt}\n\n{_JSON_INSTRUCTION}"
        payload: dict[str, Any] = {
            "model": self.model_name,
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": stream,
            "options": {
                "temperature": spec.temperature,
                "num_predict": spec.max_output_tokens,
            },
        }
        if spec.json_schema:
            # Prefer schema when Ollama supports it; otherwise "json" mode.
            payload["format"] = spec.json_schema
        return payload

    def _raise_http_error(self, exc: Exception) -> None:
        base = self.base_url
        if isinstance(exc, httpx.ConnectError):
            raise RuntimeError(
                f"Local Ollama is not reachable at {base}. "
                f"Start Ollama or set LLM_PROVIDER=mock."
            ) from exc
        if isinstance(exc, httpx.TimeoutException):
            raise RuntimeError(
                f"Ollama request timed out after {self.timeout}s. "
                f"Increase OLLAMA_REQUEST_TIMEOUT_SECONDS or use a smaller prompt."
            ) from exc
        if isinstance(exc, httpx.HTTPStatusError):
            body = ""
            try:
                body = exc.response.text.lower()
            except Exception:  # noqa: BLE001
                body = ""
            if exc.response.status_code == 404 or "not found" in body:
                raise RuntimeError(
                    f"Ollama model {self.model_name!r} is not available. "
                    f"Run: ollama pull {self.model_name}"
                ) from exc
            raise RuntimeError(
                f"Ollama HTTP {exc.response.status_code} from {base}/api/generate."
            ) from exc
        raise RuntimeError(f"Ollama provider error: {exc}") from exc

    def _parse_generate_body(self, data: dict[str, Any], spec: PromptSpec) -> LLMResponse:
        text = data.get("response") or ""
        if not isinstance(text, str):
            text = str(text)
        model = data.get("model") or self.model_name
        prompt_tokens = int(data.get("prompt_eval_count") or _estimate_tokens(
            spec.system_prompt + spec.user_prompt
        ))
        completion_tokens = int(data.get("eval_count") or _estimate_tokens(text))

        parsed: Any | None = None
        if spec.json_schema:
            parsed = _extract_json_object(text)
            if parsed is None:
                # Safe schema-minimal fallback — never pretend invalid JSON parsed.
                parsed = DeterministicMockProvider._coerce_to_schema(text, spec.json_schema)
                text = json.dumps(parsed)
                logger.warning(
                    "ollama_json_parse_failed_using_schema_fallback",
                    model=model,
                )
            else:
                text = json.dumps(parsed) if not isinstance(parsed, str) else text

        return LLMResponse(
            text=text,
            parsed_json=parsed,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            model=model,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
        retry=lambda state: (
            state.outcome is not None
            and state.outcome.failed
            and not isinstance(state.outcome.exception(), RuntimeError)
        ),
    )
    async def generate(self, spec: PromptSpec) -> LLMResponse:
        payload = self._build_payload(spec, stream=False)
        # If schema format fails on older Ollama, retry once with format=json.
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                if (
                    response.status_code >= 400
                    and spec.json_schema
                    and payload.get("format") != "json"
                ):
                    payload = dict(payload)
                    payload["format"] = "json"
                    response = await client.post(
                        f"{self.base_url}/api/generate", json=payload
                    )
                response.raise_for_status()
                data = response.json()
        except Exception as exc:  # noqa: BLE001 — normalized below
            if isinstance(exc, RuntimeError) and "Ollama" in str(exc):
                raise
            self._raise_http_error(exc)
            raise  # pragma: no cover
        return self._parse_generate_body(data, spec)

    async def stream(self, spec: PromptSpec) -> AsyncIterator[str]:
        payload = self._build_payload(spec, stream=True)
        # Streaming JSON schema mode is unreliable; stream plain text.
        payload.pop("format", None)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST", f"{self.base_url}/api/generate", json=payload
                ) as response:
                    try:
                        response.raise_for_status()
                    except httpx.HTTPStatusError as exc:
                        self._raise_http_error(exc)
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        piece = chunk.get("response") or ""
                        if piece:
                            yield piece
                        if chunk.get("done"):
                            break
        except Exception as exc:  # noqa: BLE001
            if isinstance(exc, RuntimeError) and "Ollama" in str(exc):
                raise
            self._raise_http_error(exc)


class DeterministicMockProvider(BaseLLMProvider):
    """
    Deterministic offline stand-in for the local LLM.

    Rather than returning lorem-ipsum, this mock is *content-aware*: it
    inspects `spec.json_schema` and `spec.user_prompt` to synthesize
    structurally valid, plausibly-shaped JSON so downstream Reflector /
    Aggregator logic has something real to validate against. Domain-specific
    synthesis lives in each feature's `mock_data.py`.
    """

    def __init__(self, tier: ModelTier):
        self.tier = tier
        self.model_name = f"mock-llm-{tier}"

    async def generate(self, spec: PromptSpec) -> LLMResponse:
        await asyncio.sleep(random.uniform(0.05, 0.15))

        text = self._synthesize(spec)
        parsed = None
        if spec.json_schema:
            parsed = self._coerce_to_schema(text, spec.json_schema)
            text = json.dumps(parsed)

        return LLMResponse(
            text=text,
            parsed_json=parsed,
            prompt_tokens=_estimate_tokens(spec.system_prompt + spec.user_prompt),
            completion_tokens=_estimate_tokens(text),
            model=self.model_name,
        )

    async def stream(self, spec: PromptSpec) -> AsyncIterator[str]:
        response = await self.generate(spec)
        words = response.text.split(" ")
        for i, word in enumerate(words):
            await asyncio.sleep(0.005)
            yield word + (" " if i < len(words) - 1 else "")

    @staticmethod
    def _synthesize(spec: PromptSpec) -> str:
        digest = hashlib.sha256((spec.system_prompt + spec.user_prompt).encode()).hexdigest()[:8]
        return (
            f"[mock-llm:{digest}] This is a deterministic offline response standing in for a "
            f"local Ollama call. Set LLM_PROVIDER=ollama and start Ollama "
            f"({settings.ollama_base_url}) to use the real local 8B model. "
            f"Prompt context length: {len(spec.user_prompt)} chars."
        )

    @staticmethod
    def _coerce_to_schema(_text: str, schema: dict) -> dict:
        def build(node: dict) -> Any:
            node_type = node.get("type")
            if node_type == "object":
                return {
                    key: build(sub)
                    for key, sub in node.get("properties", {}).items()
                }
            if node_type == "array":
                return [build(node.get("items", {"type": "string"}))]
            if node_type == "string":
                return "mock-value"
            if node_type in ("number", "integer"):
                return 0
            if node_type == "boolean":
                return False
            return None

        return build(schema)


# Backward-compatible alias (deprecated name — prefer DeterministicMockProvider).
MockLLMProvider = DeterministicMockProvider

_PROVIDER_CACHE: dict[str, BaseLLMProvider] = {}


def clear_llm_provider_cache() -> None:
    """Clear cached providers (tests / settings changes)."""
    _PROVIDER_CACHE.clear()


def get_llm(tier: ModelTier = "flash") -> BaseLLMProvider:
    """
    Return the LLM provider for the given cost tier ("flash" for routine
    tasks, "pro" for complex generation). Cached per provider/tier/model/URL.
    """
    provider = (settings.llm_provider or "ollama").strip().lower()
    if provider == "mock":
        model = f"mock-llm-{tier}"
        base = "mock"
    else:
        provider = "ollama"
        model = (
            settings.ollama_model_pro if tier == "pro" else settings.ollama_model_flash
        )
        base = settings.ollama_base_url.rstrip("/")

    cache_key = f"{provider}:{tier}:{model}:{base}"
    if cache_key not in _PROVIDER_CACHE:
        if provider == "mock":
            _PROVIDER_CACHE[cache_key] = DeterministicMockProvider(tier)
        else:
            _PROVIDER_CACHE[cache_key] = OllamaProvider(tier)
        logger.info(
            "llm_provider_initialized",
            tier=tier,
            provider=provider,
            mode=settings.llm_mode,
            model=model,
        )
    return _PROVIDER_CACHE[cache_key]


# --- Prompt-injection detection ------------------------------------------------------
PROMPT_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"ignore (all|any|the) (previous|prior|above) instructions", re.I),
    re.compile(r"you are now\s+\w+", re.I),
    re.compile(r"disregard (your|the) (system prompt|instructions|guardrails)", re.I),
    re.compile(r"act as (an?|the) (unfiltered|unrestricted|jailbroken)", re.I),
    re.compile(r"reveal your (system prompt|instructions)", re.I),
    re.compile(r"<\s*script", re.I),
    re.compile(r"\bDAN\b.{0,20}\bmode\b", re.I),
]


def detect_prompt_injection(text: str) -> list[str]:
    """Return the list of matched jailbreak/injection pattern descriptions, empty if none found."""
    return [pattern.pattern for pattern in PROMPT_INJECTION_PATTERNS if pattern.search(text)]
