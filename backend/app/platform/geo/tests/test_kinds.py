"""Geo domain kind enum unit tests."""

from __future__ import annotations

import pytest

from app.platform.geo import (
    GeoAreaKind,
    GeoRefError,
    JurisdictionKind,
    LocaleKind,
    WorkAuthorizationAreaKind,
    parse_geo_area_kind,
    parse_jurisdiction_kind,
    parse_locale_kind,
    parse_work_authorization_area_kind,
)


@pytest.mark.parametrize("kind", list(GeoAreaKind))
def test_geo_area_kind_accepted(kind: GeoAreaKind) -> None:
    assert parse_geo_area_kind(kind) is kind
    assert parse_geo_area_kind(kind.value) is kind


@pytest.mark.parametrize("kind", list(JurisdictionKind))
def test_jurisdiction_kind_accepted(kind: JurisdictionKind) -> None:
    assert parse_jurisdiction_kind(kind) is kind


@pytest.mark.parametrize("kind", list(LocaleKind))
def test_locale_kind_accepted(kind: LocaleKind) -> None:
    assert parse_locale_kind(kind) is kind


@pytest.mark.parametrize("kind", list(WorkAuthorizationAreaKind))
def test_work_auth_kind_accepted(kind: WorkAuthorizationAreaKind) -> None:
    assert parse_work_authorization_area_kind(kind) is kind


@pytest.mark.parametrize(
    "parser",
    [
        parse_geo_area_kind,
        parse_jurisdiction_kind,
        parse_locale_kind,
        parse_work_authorization_area_kind,
    ],
)
def test_kinds_empty_and_unknown_rejected(parser) -> None:
    with pytest.raises(GeoRefError):
        parser("")
    with pytest.raises(GeoRefError):
        parser("   ")
    with pytest.raises(GeoRefError):
        parser("not_a_real_kind")


def test_no_silent_fallback_to_unknown() -> None:
    with pytest.raises(GeoRefError):
        parse_geo_area_kind("mystery")
    assert parse_geo_area_kind("unknown") is GeoAreaKind.UNKNOWN
    with pytest.raises(GeoRefError):
        parse_jurisdiction_kind("mystery")
    assert parse_jurisdiction_kind("unknown") is JurisdictionKind.UNKNOWN
