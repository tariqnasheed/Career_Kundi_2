"""
api/routes/health.py
========================
Two probes:

- `GET /health` — fast **liveness** probe with zero dependencies on the
  database/cache, so it stays fast and still reports "healthy" during a
  transient DB blip. Consumed by Docker Compose healthchecks.
- `GET /health/deep` — **readiness** probe that actually pings the database
  and Redis and returns HTTP 503 if either is unreachable, so an orchestrator
  (Kubernetes/ECS) can gate traffic on real dependency health.
"""

import time

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db

router = APIRouter(tags=["health"])

_start_time = time.time()


@router.get("/health")
async def health_check() -> dict:
    """Return service health, name, version, and uptime in seconds (liveness)."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "uptime": round(time.time() - _start_time, 2),
    }


@router.get("/health/deep")
async def deep_health_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness probe: verify the database and Redis are actually reachable.

    Returns HTTP 200 with per-dependency `"ok"` statuses when everything is
    healthy, or HTTP 503 with the failing dependency named when something is
    down. Each check is isolated so one failing dependency still reports the
    status of the others.
    """
    checks: dict[str, str] = {}

    # --- Database -----------------------------------------------------------
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001 — report failure, never raise
        checks["database"] = f"error: {type(exc).__name__}"

    # --- Redis --------------------------------------------------------------
    # Ping a fresh short-lived client so the probe reflects Redis's CURRENT
    # state rather than whatever the cache singleton decided at boot time.
    try:
        import redis.asyncio as redis

        client = redis.from_url(settings.redis_url, decode_responses=True)
        try:
            await client.ping()
            checks["redis"] = "ok"
        finally:
            await client.aclose()
    except Exception as exc:  # noqa: BLE001 — report failure, never raise
        checks["redis"] = f"error: {type(exc).__name__}"

    all_ok = all(v == "ok" for v in checks.values())
    payload = {
        "status": "ready" if all_ok else "degraded",
        "service": settings.app_name,
        "version": settings.app_version,
        "checks": checks,
    }
    if not all_ok:
        return JSONResponse(status_code=503, content=payload)
    return payload
