"""Tests for CanonicalEntityId helpers."""

from __future__ import annotations

from uuid import UUID

import pytest

from app.platform.kernel import (
    CanonicalEntityId,
    EntityIdError,
    entity_id_to_str,
    new_entity_id,
    parse_entity_id,
)


def test_generated_id_is_uuid_compatible() -> None:
    eid = new_entity_id()
    assert isinstance(eid, UUID)
    UUID(str(eid))



def test_generated_ids_are_not_constant() -> None:
    a = new_entity_id()
    b = new_entity_id()
    c = new_entity_id()
    assert len({a, b, c}) == 3


def test_parse_uuid_object() -> None:
    raw = UUID("550e8400-e29b-41d4-a716-446655440000")
    assert parse_entity_id(raw) == CanonicalEntityId(raw)


def test_parse_canonical_string() -> None:
    s = "550e8400-e29b-41d4-a716-446655440000"
    assert parse_entity_id(s) == CanonicalEntityId(UUID(s))


def test_string_round_trip() -> None:
    eid = new_entity_id()
    text = entity_id_to_str(eid)
    assert text == str(eid)
    assert text == text.lower()
    assert parse_entity_id(text) == eid


def test_malformed_string_rejected() -> None:
    with pytest.raises(EntityIdError):
        parse_entity_id("not-a-uuid")


def test_empty_string_rejected() -> None:
    with pytest.raises(EntityIdError):
        parse_entity_id("")


def test_whitespace_only_rejected() -> None:
    with pytest.raises(EntityIdError):
        parse_entity_id("   ")


def test_integer_rejected() -> None:
    with pytest.raises(EntityIdError):
        parse_entity_id(12345)  # type: ignore[arg-type]


def test_none_rejected() -> None:
    with pytest.raises(EntityIdError):
        parse_entity_id(None)  # type: ignore[arg-type]
