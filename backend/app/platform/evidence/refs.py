"""
Evidence reference value objects (0053-F2).

Pure Python — no SQLAlchemy, FastAPI, Pydantic, or feature-domain imports.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.platform.kernel.ids import (
    CanonicalEntityId,
    EntityIdError,
    parse_entity_id,
)


class EvidenceRefError(ValueError):
    """Invalid EvidenceRef / evidence enum / contract input."""


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    """Private evidence metadata reference (not verification)."""

    evidence_id: CanonicalEntityId

    def __post_init__(self) -> None:
        try:
            object.__setattr__(self, "evidence_id", parse_entity_id(self.evidence_id))
        except EntityIdError as exc:
            raise EvidenceRefError(str(exc)) from exc
