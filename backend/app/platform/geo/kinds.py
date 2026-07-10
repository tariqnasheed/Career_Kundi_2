"""
Controlled kind contracts for geo domain (0050-PF6-S1).

No silent fallback to UNKNOWN. No auto-guess across domains.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TypeVar

from app.platform.geo.refs import GeoRefError

_E = TypeVar("_E", bound=StrEnum)


class GeoAreaKind(StrEnum):
    COUNTRY = "country"
    REGION = "region"
    CITY = "city"
    METRO_AREA = "metro_area"
    REMOTE_REGION = "remote_region"
    CAMPUS = "campus"
    CUSTOM_AREA = "custom_area"
    UNKNOWN = "unknown"


class JurisdictionKind(StrEnum):
    COUNTRY = "country"
    STATE_REGION = "state_region"
    CITY_LOCAL = "city_local"
    SUPRANATIONAL = "supranational"
    IMMIGRATION_AREA = "immigration_area"
    EMPLOYMENT_LAW_AREA = "employment_law_area"
    TAX_AREA = "tax_area"
    EDUCATION_AUTHORITY = "education_authority"
    CUSTOM_JURISDICTION = "custom_jurisdiction"
    UNKNOWN = "unknown"


class LocaleKind(StrEnum):
    LANGUAGE = "language"
    LANGUAGE_REGION = "language_region"
    CURRENCY_FORMAT = "currency_format"
    DATE_TIME_FORMAT = "date_time_format"
    MEASUREMENT_SYSTEM = "measurement_system"
    UI_LOCALE = "ui_locale"
    CUSTOM_LOCALE = "custom_locale"
    UNKNOWN = "unknown"


class WorkAuthorizationAreaKind(StrEnum):
    COUNTRY = "country"
    REGIONAL_BLOC = "regional_bloc"
    IMMIGRATION_AREA = "immigration_area"
    CUSTOM_AUTHORIZATION_AREA = "custom_authorization_area"
    UNKNOWN = "unknown"


def _parse_enum(enum_cls: type[_E], value: object, label: str) -> _E:
    if isinstance(value, enum_cls):
        return value
    if not isinstance(value, str):
        raise GeoRefError(
            f"{label} must be str or {enum_cls.__name__}; got {type(value).__name__}"
        )
    cleaned = value.strip()
    if not cleaned:
        raise GeoRefError(f"{label} must not be empty")
    try:
        return enum_cls(cleaned)
    except ValueError as exc:
        raise GeoRefError(f"unknown {label}: {value!r}") from exc


def parse_geo_area_kind(value: object) -> GeoAreaKind:
    return _parse_enum(GeoAreaKind, value, "geo_kind")


def parse_jurisdiction_kind(value: object) -> JurisdictionKind:
    return _parse_enum(JurisdictionKind, value, "jurisdiction_kind")


def parse_locale_kind(value: object) -> LocaleKind:
    return _parse_enum(LocaleKind, value, "locale_kind")


def parse_work_authorization_area_kind(value: object) -> WorkAuthorizationAreaKind:
    return _parse_enum(
        WorkAuthorizationAreaKind, value, "authorization_kind"
    )
