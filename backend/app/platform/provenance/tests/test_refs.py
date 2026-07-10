"""SourceRef / SnapshotRef / SourceKind unit tests."""

from __future__ import annotations

import pytest

from app.platform.kernel import new_entity_id
from app.platform.provenance import (
    ProvenanceRefError,
    SnapshotRef,
    SourceKind,
    SourceRef,
    parse_source_kind,
)


def test_source_ref_valid() -> None:
    sid = new_entity_id()
    ref = SourceRef(source_id=sid)
    assert ref.source_id == sid


def test_source_ref_immutable() -> None:
    ref = SourceRef(source_id=new_entity_id())
    with pytest.raises(AttributeError):
        ref.source_id = new_entity_id()  # type: ignore[misc]


def test_source_ref_malformed_rejected() -> None:
    with pytest.raises(ProvenanceRefError):
        SourceRef(source_id="not-a-uuid")  # type: ignore[arg-type]


def test_snapshot_ref_valid() -> None:
    sid = new_entity_id()
    ref = SnapshotRef(snapshot_id=sid)
    assert ref.snapshot_id == sid


def test_snapshot_ref_immutable() -> None:
    ref = SnapshotRef(snapshot_id=new_entity_id())
    with pytest.raises(AttributeError):
        ref.snapshot_id = new_entity_id()  # type: ignore[misc]


def test_snapshot_ref_malformed_rejected() -> None:
    with pytest.raises(ProvenanceRefError):
        SnapshotRef(snapshot_id="bad")  # type: ignore[arg-type]


@pytest.mark.parametrize("kind", list(SourceKind))
def test_source_kind_accepted(kind: SourceKind) -> None:
    assert parse_source_kind(kind) is kind
    assert parse_source_kind(kind.value) is kind


def test_source_kind_empty_rejected() -> None:
    with pytest.raises(ProvenanceRefError):
        parse_source_kind("")
    with pytest.raises(ProvenanceRefError):
        parse_source_kind("   ")


def test_source_kind_unknown_rejected() -> None:
    with pytest.raises(ProvenanceRefError):
        parse_source_kind("verified")
    with pytest.raises(ProvenanceRefError):
        parse_source_kind("unknown_kind")


def test_fallback_not_silently_upgraded() -> None:
    assert parse_source_kind("fallback") is SourceKind.FALLBACK
    with pytest.raises(ProvenanceRefError):
        parse_source_kind("verified")
