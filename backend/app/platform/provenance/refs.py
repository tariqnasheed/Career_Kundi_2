"""
Provenance reference value objects (0050-PF4-S1).

Pure Python — no SQLAlchemy, FastAPI, Pydantic, or feature-domain imports.
Source != Snapshot. Refs carry canonical IDs only.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.platform.kernel.ids import (
    CanonicalEntityId,
    EntityIdError,
    parse_entity_id,
)


class SourceKind(StrEnum):
    """Approved provenance source ladder kinds (no confidence/verification)."""

    USER = "user"
    URL = "url"
    COMPANY = "company"
    DOCUMENT = "document"
    MODEL = "model"
    SYSTEM = "system"
    FALLBACK = "fallback"


class ProvenanceRefError(ValueError):
    """Invalid SourceRef / SnapshotRef / SourceKind input."""


def parse_source_kind(value: object) -> SourceKind:
    """Require a known SourceKind; reject empty and unknown values."""
    if isinstance(value, SourceKind):
        return value
    if not isinstance(value, str):
        raise ProvenanceRefError(
            f"source_kind must be str or SourceKind; got {type(value).__name__}"
        )
    cleaned = value.strip()
    if not cleaned:
        raise ProvenanceRefError("source_kind must not be empty")
    try:
        return SourceKind(cleaned)
    except ValueError as exc:
        raise ProvenanceRefError(f"unknown source_kind: {value!r}") from exc


@dataclass(frozen=True, slots=True)
class SourceRef:
    """Origin/channel of information (not a captured observation)."""

    source_id: CanonicalEntityId

    def __post_init__(self) -> None:
        try:
            object.__setattr__(self, "source_id", parse_entity_id(self.source_id))
        except EntityIdError as exc:
            raise ProvenanceRefError(str(exc)) from exc


@dataclass(frozen=True, slots=True)
class SnapshotRef:
    """Captured observation of a source at a point in time."""

    snapshot_id: CanonicalEntityId

    def __post_init__(self) -> None:
        try:
            object.__setattr__(self, "snapshot_id", parse_entity_id(self.snapshot_id))
        except EntityIdError as exc:
            raise ProvenanceRefError(str(exc)) from exc
