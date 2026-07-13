"""
core/errors.py
=================
Structured application error hierarchy + FastAPI exception handlers.

Every API error returned by this backend follows the same JSON envelope:

    {
        "error": true,
        "code": "JOB_SCRAPE_FAILED",
        "message": "Could not reach the job posting URL.",
        "details": {"url": "...", "status_code": 404}
    }

This makes frontend error handling uniform (one `ApiError` type, see
frontend/src/lib/api.ts) and gives the Cost Monitor / audit log a single
shape to record regardless of which layer raised the error.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger(__name__)


class CareerkundiError(Exception):
    """
    Base class for every domain-specific error raised in this codebase.

    Subclasses set a machine-readable `code`, a human-readable `message`,
    an HTTP `status_code`, and optional structured `details`. Raising any
    `CareerkundiError` subclass anywhere in a route or agent automatically
    produces the standard error envelope via the handler registered in
    `register_exception_handlers` below — no per-route try/except needed.
    """

    code: str = "INTERNAL_ERROR"
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class NotFoundError(CareerkundiError):
    code = "NOT_FOUND"
    status_code = status.HTTP_404_NOT_FOUND


class ValidationFailedError(CareerkundiError):
    code = "VALIDATION_FAILED"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class AuthenticationError(CareerkundiError):
    code = "AUTHENTICATION_FAILED"
    status_code = status.HTTP_401_UNAUTHORIZED


class AuthorizationError(CareerkundiError):
    code = "FORBIDDEN"
    status_code = status.HTTP_403_FORBIDDEN


class ConflictError(CareerkundiError):
    code = "CONFLICT"
    status_code = status.HTTP_409_CONFLICT


class RateLimitedError(CareerkundiError):
    code = "RATE_LIMITED"
    status_code = status.HTTP_429_TOO_MANY_REQUESTS


class GuardrailRejectionError(CareerkundiError):
    """Raised by a Guardrail agent when input fails safety/sanity checks."""

    code = "GUARDRAIL_REJECTED"
    status_code = status.HTTP_400_BAD_REQUEST


class ReflectorRejectionError(CareerkundiError):
    """Raised when an Executor's output fails Reflector validation after max revision rounds."""

    code = "QUALITY_GATE_FAILED"
    status_code = status.HTTP_502_BAD_GATEWAY


class ScrapingFailedError(CareerkundiError):
    code = "SCRAPING_FAILED"
    status_code = status.HTTP_502_BAD_GATEWAY


class TokenBudgetExceededError(CareerkundiError):
    """Raised by the CostMonitorAgent when a request would exceed its allocated token budget."""

    code = "TOKEN_BUDGET_EXCEEDED"
    status_code = status.HTTP_402_PAYMENT_REQUIRED


def _error_envelope(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build the standard `{error, code, message, details}` response body."""
    return {"error": True, "code": code, "message": message, "details": details or {}}


def register_exception_handlers(app: FastAPI) -> None:
    """
    Attach global exception handlers to the FastAPI app.

    Called once from `app.main` during app construction. Ensures NO
    unhandled exception ever reaches the client as a raw 500 stack trace —
    everything is normalized to the standard error envelope and logged with
    full context first.
    """

    @app.exception_handler(CareerkundiError)
    async def handle_careerkundi_error(request: Request, exc: CareerkundiError) -> JSONResponse:
        # This catches any of our custom errors (like NotFoundError or AuthenticationError)
        # We log it as a warning so we can track issues in our server logs
        logger.warning(
            "request_failed",
            code=exc.code,
            message=exc.message,
            path=request.url.path,
            details=exc.details,
        )
        # Then we return the error to the user in our standard JSON format
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_envelope(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        # This catches errors when a user sends bad data (e.g., missing a required field)
        # FastAPI raises this automatically before our route code even runs!
        safe_errors: list[dict[str, Any]] = []
        for err in exc.errors():
            safe_errors.append(
                {
                    "loc": [str(part) for part in err.get("loc", ())],
                    "msg": str(err.get("msg", "validation error")),
                    "type": str(err.get("type", "value_error")),
                }
            )
        logger.warning("request_validation_failed", path=request.url.path, errors=safe_errors)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_envelope(
                "VALIDATION_FAILED",
                "The request body failed validation.",
                {"errors": safe_errors},
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_exception", path=request.url.path, error=str(exc), exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_envelope(
                "INTERNAL_ERROR",
                "Something went wrong on our end. The team has been notified.",
            ),
        )
