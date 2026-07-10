"""
Privacy reference value objects (0050-PF9-S1).

Pure Python — no SQLAlchemy, FastAPI, Pydantic, or feature-domain imports.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.platform.kernel.ids import (
    CanonicalEntityId,
    EntityIdError,
    parse_entity_id,
)


class PrivacyRefError(ValueError):
    """Invalid privacy ref / kind input."""


@dataclass(frozen=True, slots=True)
class PrivacyPolicyRef:
    privacy_policy_id: CanonicalEntityId

    def __post_init__(self) -> None:
        try:
            object.__setattr__(
                self, "privacy_policy_id", parse_entity_id(self.privacy_policy_id)
            )
        except EntityIdError as exc:
            raise PrivacyRefError(str(exc)) from exc


@dataclass(frozen=True, slots=True)
class ConsentRecordRef:
    consent_record_id: CanonicalEntityId

    def __post_init__(self) -> None:
        try:
            object.__setattr__(
                self, "consent_record_id", parse_entity_id(self.consent_record_id)
            )
        except EntityIdError as exc:
            raise PrivacyRefError(str(exc)) from exc


@dataclass(frozen=True, slots=True)
class RetentionPolicyRef:
    retention_policy_id: CanonicalEntityId

    def __post_init__(self) -> None:
        try:
            object.__setattr__(
                self,
                "retention_policy_id",
                parse_entity_id(self.retention_policy_id),
            )
        except EntityIdError as exc:
            raise PrivacyRefError(str(exc)) from exc
