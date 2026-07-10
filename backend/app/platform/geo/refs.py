"""
Geo / jurisdiction / locale / work-authorization area refs (0050-PF6-S1).

Pure Python — no SQLAlchemy, FastAPI, Pydantic, or feature-domain imports.
Geography ≠ jurisdiction ≠ locale ≠ work-authorization area.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.platform.kernel.ids import (
    CanonicalEntityId,
    EntityIdError,
    parse_entity_id,
)


class GeoRefError(ValueError):
    """Invalid geo/jurisdiction/locale/authorization ref or kind input."""


@dataclass(frozen=True, slots=True)
class GeoRef:
    """Physical/logistical place or area (not jurisdiction or locale)."""

    geo_id: CanonicalEntityId

    def __post_init__(self) -> None:
        try:
            object.__setattr__(self, "geo_id", parse_entity_id(self.geo_id))
        except EntityIdError as exc:
            raise GeoRefError(str(exc)) from exc


@dataclass(frozen=True, slots=True)
class JurisdictionRef:
    """Legal/regulatory authority area (not a physical place)."""

    jurisdiction_id: CanonicalEntityId

    def __post_init__(self) -> None:
        try:
            object.__setattr__(
                self, "jurisdiction_id", parse_entity_id(self.jurisdiction_id)
            )
        except EntityIdError as exc:
            raise GeoRefError(str(exc)) from exc


@dataclass(frozen=True, slots=True)
class LocaleRef:
    """Presentation/language/format preference (not geography)."""

    locale_id: CanonicalEntityId

    def __post_init__(self) -> None:
        try:
            object.__setattr__(self, "locale_id", parse_entity_id(self.locale_id))
        except EntityIdError as exc:
            raise GeoRefError(str(exc)) from exc


@dataclass(frozen=True, slots=True)
class WorkAuthorizationAreaRef:
    """Future-safe work-authorization area reference (not status/visa)."""

    authorization_area_id: CanonicalEntityId

    def __post_init__(self) -> None:
        try:
            object.__setattr__(
                self,
                "authorization_area_id",
                parse_entity_id(self.authorization_area_id),
            )
        except EntityIdError as exc:
            raise GeoRefError(str(exc)) from exc
