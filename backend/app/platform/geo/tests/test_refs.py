"""Geo / jurisdiction / locale / work-authorization ref unit tests."""

from __future__ import annotations

import pytest

from app.platform.geo import (
    GeoRef,
    GeoRefError,
    JurisdictionRef,
    LocaleRef,
    WorkAuthorizationAreaRef,
)
from app.platform.kernel import new_entity_id


def test_geo_ref_valid() -> None:
    gid = new_entity_id()
    assert GeoRef(geo_id=gid).geo_id == gid


def test_geo_ref_immutable() -> None:
    ref = GeoRef(geo_id=new_entity_id())
    with pytest.raises(AttributeError):
        ref.geo_id = new_entity_id()  # type: ignore[misc]


def test_geo_ref_malformed_rejected() -> None:
    with pytest.raises(GeoRefError):
        GeoRef(geo_id="bad")  # type: ignore[arg-type]


def test_jurisdiction_ref_valid() -> None:
    jid = new_entity_id()
    assert JurisdictionRef(jurisdiction_id=jid).jurisdiction_id == jid


def test_jurisdiction_ref_immutable() -> None:
    ref = JurisdictionRef(jurisdiction_id=new_entity_id())
    with pytest.raises(AttributeError):
        ref.jurisdiction_id = new_entity_id()  # type: ignore[misc]


def test_jurisdiction_ref_malformed_rejected() -> None:
    with pytest.raises(GeoRefError):
        JurisdictionRef(jurisdiction_id="bad")  # type: ignore[arg-type]


def test_locale_ref_valid() -> None:
    lid = new_entity_id()
    assert LocaleRef(locale_id=lid).locale_id == lid


def test_locale_ref_immutable() -> None:
    ref = LocaleRef(locale_id=new_entity_id())
    with pytest.raises(AttributeError):
        ref.locale_id = new_entity_id()  # type: ignore[misc]


def test_locale_ref_malformed_rejected() -> None:
    with pytest.raises(GeoRefError):
        LocaleRef(locale_id="bad")  # type: ignore[arg-type]


def test_work_auth_ref_valid() -> None:
    aid = new_entity_id()
    assert (
        WorkAuthorizationAreaRef(authorization_area_id=aid).authorization_area_id
        == aid
    )


def test_work_auth_ref_immutable() -> None:
    ref = WorkAuthorizationAreaRef(authorization_area_id=new_entity_id())
    with pytest.raises(AttributeError):
        ref.authorization_area_id = new_entity_id()  # type: ignore[misc]


def test_work_auth_ref_malformed_rejected() -> None:
    with pytest.raises(GeoRefError):
        WorkAuthorizationAreaRef(authorization_area_id="bad")  # type: ignore[arg-type]
