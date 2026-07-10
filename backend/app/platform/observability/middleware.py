"""
Request correlation + completion logging middleware (0050-PF10-S1).

Logs safe request metadata only — never bodies, cookies, or auth headers.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.platform.observability.correlation import (
    CORRELATION_HEADER,
    normalize_correlation_id,
)
from app.platform.observability.events import make_event
from app.platform.observability.logging import get_platform_logger, log_event

_logger = get_platform_logger("app.platform.observability.middleware")


def _request_path(request: Request) -> str:
    route = request.scope.get("route")
    template = getattr(route, "path", None) if route is not None else None
    if isinstance(template, str) and template:
        return template
    return request.url.path


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Normalize X-Request-ID, time the request, log request_completed."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        incoming = request.headers.get("x-request-id")
        correlation_id = normalize_correlation_id(incoming)
        request.state.correlation_id = correlation_id

        # Preserve existing structlog request-scoped binding for in-request logs.
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=correlation_id,
            method=request.method,
            path=_request_path(request),
        )

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        response.headers[CORRELATION_HEADER] = correlation_id

        event = make_event(
            "request_completed",
            correlation_id,
            {
                "method": request.method,
                "path": _request_path(request),
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "correlation_id": correlation_id,
            },
        )
        log_event(_logger, logging.INFO, event)
        return response
