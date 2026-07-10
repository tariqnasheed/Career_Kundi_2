"""ObservabilityEvent contract tests (0050-PF10-S1)."""

from __future__ import annotations

import dataclasses

import pytest

from app.platform.observability.correlation import is_valid_correlation_id
from app.platform.observability.events import (
    MAX_EVENT_NAME_LENGTH,
    ObservabilityError,
    ObservabilityEvent,
    make_event,
)
from app.platform.observability.redaction import REDACTED_MARKER


def test_event_name_required() -> None:
    with pytest.raises(ObservabilityError):
        make_event("", "abc-123")
    with pytest.raises(ObservabilityError):
        make_event("   ", "abc-123")


def test_event_name_length_bounded() -> None:
    with pytest.raises(ObservabilityError):
        make_event("e" * (MAX_EVENT_NAME_LENGTH + 1), "abc-123")


def test_correlation_normalized() -> None:
    event = make_event("ping", "bad id with spaces")
    assert is_valid_correlation_id(event.correlation_id)
    assert event.correlation_id != "bad id with spaces"


def test_attributes_redacted() -> None:
    event = make_event(
        "ping",
        "corr-1",
        {"password": "x", "method": "GET"},
    )
    assert event.attributes["password"] == REDACTED_MARKER
    assert event.attributes["method"] == "GET"


def test_to_log_dict_includes_name_and_correlation() -> None:
    event = make_event("request_completed", "corr-1", {"status_code": 200})
    payload = event.to_log_dict()
    assert payload["event_name"] == "request_completed"
    assert payload["correlation_id"] == "corr-1"
    assert payload["attributes"]["status_code"] == 200


def test_event_immutable() -> None:
    event = make_event("ping", "corr-1", {"a": 1})
    assert isinstance(event, ObservabilityEvent)
    with pytest.raises((AttributeError, TypeError, dataclasses.FrozenInstanceError)):
        event.event_name = "other"  # type: ignore[misc]
    with pytest.raises(TypeError):
        event.attributes["a"] = 2  # type: ignore[index]
