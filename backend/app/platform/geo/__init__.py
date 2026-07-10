"""
CareerKundi geo / jurisdiction / locale domain (0050-PF6-S1).

Public exports are refs and kind enums/parsers.
Persistence/service live in sibling modules and db models.
"""

from app.platform.geo.kinds import (
    GeoAreaKind,
    JurisdictionKind,
    LocaleKind,
    WorkAuthorizationAreaKind,
    parse_geo_area_kind,
    parse_jurisdiction_kind,
    parse_locale_kind,
    parse_work_authorization_area_kind,
)
from app.platform.geo.refs import (
    GeoRef,
    GeoRefError,
    JurisdictionRef,
    LocaleRef,
    WorkAuthorizationAreaRef,
)

__all__ = [
    "GeoAreaKind",
    "GeoRef",
    "GeoRefError",
    "JurisdictionKind",
    "JurisdictionRef",
    "LocaleKind",
    "LocaleRef",
    "WorkAuthorizationAreaKind",
    "WorkAuthorizationAreaRef",
    "parse_geo_area_kind",
    "parse_jurisdiction_kind",
    "parse_locale_kind",
    "parse_work_authorization_area_kind",
]
