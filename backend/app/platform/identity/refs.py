"""
Identity reference value objects (0050-PF3-S1).

Pure Python — no SQLAlchemy, FastAPI, Pydantic, or feature-domain imports.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.platform.kernel.ids import (
    CanonicalEntityId,
    EntityIdError,
    parse_entity_id,
)


class ActorType(StrEnum):
    USER = "user"
    SYSTEM = "system"
    SERVICE = "service"
    ORGANIZATION_MEMBER = "organization_member"


class IdentityRefError(ValueError):
    """Invalid ActorRef / SubjectRef / OrganizationRef input."""


@dataclass(frozen=True, slots=True)
class ActorRef:
    """Who is performing an action (not the career subject of records)."""

    actor_type: ActorType
    actor_id: CanonicalEntityId

    def __post_init__(self) -> None:
        if not isinstance(self.actor_type, ActorType):
            raise IdentityRefError(
                f"actor_type must be ActorType; got {type(self.actor_type).__name__}"
            )
        try:
            object.__setattr__(self, "actor_id", parse_entity_id(self.actor_id))
        except EntityIdError as exc:
            raise IdentityRefError(str(exc)) from exc


@dataclass(frozen=True, slots=True)
class SubjectRef:
    """Career subject identity reference (not a User account)."""

    subject_id: CanonicalEntityId

    def __post_init__(self) -> None:
        try:
            object.__setattr__(self, "subject_id", parse_entity_id(self.subject_id))
        except EntityIdError as exc:
            raise IdentityRefError(str(exc)) from exc


@dataclass(frozen=True, slots=True)
class OrganizationRef:
    """Future-safe organization reference stub (no org table in PF3-S1)."""

    organization_id: CanonicalEntityId

    def __post_init__(self) -> None:
        try:
            object.__setattr__(
                self, "organization_id", parse_entity_id(self.organization_id)
            )
        except EntityIdError as exc:
            raise IdentityRefError(str(exc)) from exc
