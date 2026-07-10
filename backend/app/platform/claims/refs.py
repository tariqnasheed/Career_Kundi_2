"""
Claim reference value objects (0050-PF5-S1).

Pure Python — no SQLAlchemy, FastAPI, Pydantic, or feature-domain imports.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.platform.kernel.ids import (
    CanonicalEntityId,
    EntityIdError,
    parse_entity_id,
)


class ClaimRefError(ValueError):
    """Invalid ClaimRef / claim enum input."""


@dataclass(frozen=True, slots=True)
class ClaimRef:
    """Statement asserted about a subject (not evidence or verification)."""

    claim_id: CanonicalEntityId

    def __post_init__(self) -> None:
        try:
            object.__setattr__(self, "claim_id", parse_entity_id(self.claim_id))
        except EntityIdError as exc:
            raise ClaimRefError(str(exc)) from exc
