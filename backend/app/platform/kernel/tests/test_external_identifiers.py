"""Tests for ExternalIdentifier."""

from __future__ import annotations

import pytest

from app.platform.kernel import ExternalIdentifier
from app.platform.kernel.external_identifiers import ExternalIdentifierError


def test_valid_system_value() -> None:
    ext = ExternalIdentifier(system="esco", value="http://data.europa.eu/esco/occupation/1")
    assert ext.system == "esco"
    assert ext.value.startswith("http://")
    assert ext.version is None


def test_optional_version_absent() -> None:
    ext = ExternalIdentifier(system="onet", value="15-1252.00")
    assert ext.version is None


def test_optional_version_present() -> None:
    ext = ExternalIdentifier(system="esco", value="occ-1", version="v1.2.0")
    assert ext.version == "v1.2.0"


def test_immutable() -> None:
    ext = ExternalIdentifier(system="isco", value="2512")
    with pytest.raises(AttributeError):
        ext.system = "other"  # type: ignore[misc]


def test_empty_system_rejected() -> None:
    with pytest.raises(ExternalIdentifierError):
        ExternalIdentifier(system="", value="x")


def test_whitespace_system_rejected() -> None:
    with pytest.raises(ExternalIdentifierError):
        ExternalIdentifier(system="  ", value="x")


def test_empty_value_rejected() -> None:
    with pytest.raises(ExternalIdentifierError):
        ExternalIdentifier(system="esco", value="")


def test_whitespace_value_rejected() -> None:
    with pytest.raises(ExternalIdentifierError):
        ExternalIdentifier(system="esco", value="   ")


def test_supplied_empty_version_rejected() -> None:
    with pytest.raises(ExternalIdentifierError):
        ExternalIdentifier(system="esco", value="occ-1", version="")
    with pytest.raises(ExternalIdentifierError):
        ExternalIdentifier(system="esco", value="occ-1", version="  ")


def test_case_and_value_preservation() -> None:
    ext = ExternalIdentifier(system="O*NET", value="AbC-123")
    assert ext.system == "O*NET"
    assert ext.value == "AbC-123"
