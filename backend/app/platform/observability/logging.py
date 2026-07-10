"""
Structured logging helpers for platform observability (0050-PF10-S1).

Does not globally rewrite application logging configuration.
"""

from __future__ import annotations

import json
import logging

from app.platform.observability.events import ObservabilityEvent


def get_platform_logger(name: str) -> logging.Logger:
    """Return a stdlib logger for platform observability events."""
    return logging.getLogger(name)


def log_event(
    logger: logging.Logger, level: int, event: ObservabilityEvent
) -> None:
    """Emit a structured, redacted observability event payload."""
    if not isinstance(event, ObservabilityEvent):
        raise TypeError("event must be ObservabilityEvent")
    payload = event.to_log_dict()
    logger.log(level, json.dumps(payload, default=str, sort_keys=True))
