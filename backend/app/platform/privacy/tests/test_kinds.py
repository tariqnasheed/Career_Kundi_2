"""Privacy kind unit tests."""

from __future__ import annotations

import pytest

from app.platform.privacy import (
    ConsentStatus,
    DataClassification,
    PrivacyRefError,
    ProcessingPurpose,
    RetentionCategory,
    VisibilityScope,
    parse_consent_status,
    parse_data_classification,
    parse_processing_purpose,
    parse_retention_category,
    parse_visibility_scope,
)

_PARSERS = [
    (DataClassification, parse_data_classification),
    (VisibilityScope, parse_visibility_scope),
    (ProcessingPurpose, parse_processing_purpose),
    (ConsentStatus, parse_consent_status),
    (RetentionCategory, parse_retention_category),
]


@pytest.mark.parametrize(("enum_cls", "parser"), _PARSERS)
def test_known_values_accepted(enum_cls, parser) -> None:
    for member in enum_cls:
        assert parser(member) is member
        assert parser(member.value) is member


@pytest.mark.parametrize(("enum_cls", "parser"), _PARSERS)
def test_empty_and_unknown_rejected(enum_cls, parser) -> None:
    with pytest.raises(PrivacyRefError):
        parser("")
    with pytest.raises(PrivacyRefError):
        parser("   ")
    with pytest.raises(PrivacyRefError):
        parser("not_a_real_value")


def test_no_silent_fallback_to_unknown() -> None:
    with pytest.raises(PrivacyRefError):
        parse_data_classification("mystery")
    assert parse_data_classification("unknown") is DataClassification.UNKNOWN
