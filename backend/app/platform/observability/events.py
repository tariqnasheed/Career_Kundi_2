"""
Safe observability event primitives (0050-PF10-S1).

Operational events only — not legal audit records.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from app.platform.observability.correlation import normalize_correlation_id
from app.platform.observability.redaction import redact_mapping

MAX_EVENT_NAME_LENGTH = 128


class ObservabilityError(ValueError):
    """Invalid observability event input."""


@dataclass(frozen=True, slots=True)
class ObservabilityEvent:
    event_name: str
    correlation_id: str
    attributes: Mapping[str, Any]

    def to_log_dict(self) -> dict[str, Any]:
        return {
            "event_name": self.event_name,
            "correlation_id": self.correlation_id,
            "attributes": dict(self.attributes),
        }


def make_event(
    event_name: str,
    correlation_id: str | None,
    attributes: Mapping[str, Any] | None = None,
) -> ObservabilityEvent:
    if not isinstance(event_name, str):
        raise ObservabilityError("event_name must be str")
    cleaned_name = event_name.strip()
    if not cleaned_name:
        raise ObservabilityError("event_name must not be empty")
    if len(cleaned_name) > MAX_EVENT_NAME_LENGTH:
        raise ObservabilityError(
            f"event_name exceeds max length {MAX_EVENT_NAME_LENGTH}"
        )
    cid = normalize_correlation_id(correlation_id)
    raw_attrs: Mapping[str, Any] = attributes if attributes is not None else {}
    if not isinstance(raw_attrs, Mapping):
        raise ObservabilityError("attributes must be a Mapping")
    redacted = redact_mapping(raw_attrs)
    return ObservabilityEvent(
        event_name=cleaned_name,
        correlation_id=cid,
        attributes=MappingProxyType(redacted),
    )
