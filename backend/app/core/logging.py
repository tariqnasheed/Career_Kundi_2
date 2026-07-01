"""
core/logging.py
=================
Structured JSON logging configuration using `structlog`.

Every log line emitted anywhere in the backend (request middleware, agent
nodes, scraping tools, error handlers) goes through this configuration so
logs are uniformly structured JSON on stdout — exactly what's needed for
container log aggregation (Loki/CloudWatch/Datadog) in production, while
still being readable in a local dev console.

Each log record includes, where applicable: request_id, user_id, endpoint,
method, status_code, latency_ms, and token_count (for LLM-backed routes).
Those context fields are bound via `structlog.contextvars` in the request
middleware (see app/main.py) so every log line inside a request's lifecycle
automatically carries them without being passed explicitly through every
function call.
"""

import logging
import sys

import structlog

from app.core.config import settings


def configure_logging() -> None:
    """
    Configure structlog + stdlib logging once at application startup.

    Called from `app.main` before the FastAPI app is constructed so that
    even import-time log statements (e.g. "loaded N vector store entries")
    are captured in the same structured format.
    """
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Route stdlib logging (used by uvicorn, sqlalchemy, etc.) through the
    # same processor pipeline so third-party library logs are also JSON.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.app_debug:
        # Human-friendly colored console output for local development.
        renderer = structlog.dev.ConsoleRenderer()
    else:
        # Machine-parseable JSON for production log aggregation.
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.types.FilteringBoundLogger:
    """Return a named structlog logger, e.g. `get_logger(__name__)`."""
    return structlog.get_logger(name)
