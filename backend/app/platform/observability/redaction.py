"""
Privacy-aware redaction helpers (0050-PF10-S1).

Log metadata, not user content. No advanced PII detection in this slice.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

REDACTED_MARKER = "[REDACTED]"

_SENSITIVE_KEYS = frozenset(
    {
        "password",
        "token",
        "access_token",
        "refresh_token",
        "authorization",
        "cookie",
        "set_cookie",
        "secret",
        "api_key",
        "apikey",
        "client_secret",
        "session",
        "jwt",
        "claim_value",
        "cv_text",
        "resume_text",
        "profile_bio",
        "email_body",
        "document_text",
        "llm_prompt",
        "llm_response",
    }
)


def _normalize_key(key: str) -> str:
    return key.strip().lower().replace("-", "_")


def _is_sensitive_key(key: str) -> bool:
    return _normalize_key(key) in _SENSITIVE_KEYS


def redact_value(key: str, value: Any) -> Any:
    """Redact a single value when its key is sensitive; recurse into containers."""
    if _is_sensitive_key(key):
        return REDACTED_MARKER
    return _redact_container(value)


def _redact_container(value: Any) -> Any:
    if isinstance(value, Mapping):
        return redact_mapping(value)
    if isinstance(value, list):
        return [_redact_container(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact_container(item) for item in value)
    return value


def redact_mapping(mapping: Mapping[str, Any]) -> dict[str, Any]:
    """Return a new dict with sensitive keys redacted. Does not mutate input."""
    if not isinstance(mapping, Mapping):
        raise TypeError("mapping must be a Mapping")
    out: dict[str, Any] = {}
    for key, value in mapping.items():
        key_str = str(key)
        if _is_sensitive_key(key_str):
            out[key_str] = REDACTED_MARKER
        else:
            out[key_str] = _redact_container(value)
    return out
