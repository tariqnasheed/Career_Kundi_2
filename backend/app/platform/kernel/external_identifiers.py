"""
External system identifiers (0050-PF2-S1).

Distinct from CanonicalEntityId — these are IDs assigned by external systems
(ESCO, O*NET, ISCO, providers, etc.). No taxonomy mapping semantics here.
"""

from __future__ import annotations

from dataclasses import dataclass


class ExternalIdentifierError(ValueError):
    """Raised when ExternalIdentifier fields fail validation."""


@dataclass(frozen=True, slots=True)
class ExternalIdentifier:
    """Immutable external identifier value object."""

    system: str
    value: str
    version: str | None = None

    def __post_init__(self) -> None:
        system = self.system.strip() if isinstance(self.system, str) else ""
        value = self.value.strip() if isinstance(self.value, str) else ""
        if not isinstance(self.system, str) or not system:
            raise ExternalIdentifierError("system must be a non-empty string")
        if not isinstance(self.value, str) or not value:
            raise ExternalIdentifierError("value must be a non-empty string")
        # Preserve original value/system (do not lowercase). Only reject blank.
        if self.system != system or self.value != value:
            # Whitespace-only already rejected; leading/trailing whitespace is invalid.
            raise ExternalIdentifierError(
                "system and value must not have leading or trailing whitespace"
            )
        if self.version is not None:
            if not isinstance(self.version, str):
                raise ExternalIdentifierError("version must be a string or None")
            ver = self.version.strip()
            if not ver:
                raise ExternalIdentifierError("version, if supplied, must be non-empty")
            if self.version != ver:
                raise ExternalIdentifierError(
                    "version must not have leading or trailing whitespace"
                )
