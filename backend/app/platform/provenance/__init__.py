"""
CareerKundi provenance domain (0050-PF4-S1).

Public exports are reference value objects and SourceKind.
Persistence/service live in sibling modules and db models.
"""

from app.platform.provenance.refs import (
    ProvenanceRefError,
    SnapshotRef,
    SourceKind,
    SourceRef,
    parse_source_kind,
)

__all__ = [
    "ProvenanceRefError",
    "SnapshotRef",
    "SourceKind",
    "SourceRef",
    "parse_source_kind",
]
