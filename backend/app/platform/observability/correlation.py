"""
Request correlation ID helpers (0050-PF10-S1).

Correlation IDs connect logs for a request. They are not authentication,
session tokens, or authorization credentials.
"""

from __future__ import annotations

import re
import uuid

CORRELATION_HEADER = "X-Request-ID"
MAX_CORRELATION_ID_LENGTH = 128
_CORRELATION_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def new_correlation_id() -> str:
    """Return an opaque, bounded correlation ID (UUID4 hex)."""
    return uuid.uuid4().hex


def is_valid_correlation_id(value: str) -> bool:
    """Return True when value is a safe, bounded correlation ID (exact match)."""
    if not isinstance(value, str):
        return False
    if not value or value != value.strip():
        return False
    if len(value) > MAX_CORRELATION_ID_LENGTH:
        return False
    if any(ord(ch) < 32 for ch in value):
        return False
    return _CORRELATION_RE.fullmatch(value) is not None


def normalize_correlation_id(value: str | None) -> str:
    """
    Preserve a valid incoming ID; otherwise generate a fresh one.

    Leading/trailing whitespace is stripped before validation. Empty,
    unsafe, overlong, or control-bearing values are replaced.
    """
    if value is None:
        return new_correlation_id()
    if not isinstance(value, str):
        return new_correlation_id()
    cleaned = value.strip()
    if is_valid_correlation_id(cleaned):
        return cleaned
    return new_correlation_id()
