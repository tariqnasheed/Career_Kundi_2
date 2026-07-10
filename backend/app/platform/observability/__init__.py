"""
CareerKundi observability domain (0050-PF10-S1).

Public exports: correlation, redaction, events, logging helpers, middleware.
"""

from app.platform.observability.correlation import (
    CORRELATION_HEADER,
    is_valid_correlation_id,
    new_correlation_id,
    normalize_correlation_id,
)
from app.platform.observability.events import (
    ObservabilityError,
    ObservabilityEvent,
    make_event,
)
from app.platform.observability.logging import get_platform_logger, log_event
from app.platform.observability.middleware import ObservabilityMiddleware
from app.platform.observability.redaction import (
    REDACTED_MARKER,
    redact_mapping,
    redact_value,
)

__all__ = [
    "CORRELATION_HEADER",
    "ObservabilityError",
    "ObservabilityEvent",
    "ObservabilityMiddleware",
    "REDACTED_MARKER",
    "get_platform_logger",
    "is_valid_correlation_id",
    "log_event",
    "make_event",
    "new_correlation_id",
    "normalize_correlation_id",
    "redact_mapping",
    "redact_value",
]
