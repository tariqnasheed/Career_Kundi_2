"""Claim kind and status-axis unit tests."""

from __future__ import annotations

import pytest

from app.platform.claims import (
    ClaimKind,
    ClaimOrigin,
    ClaimRefError,
    SupportStatus,
    VerificationStatus,
    parse_claim_kind,
    parse_claim_origin,
    parse_support_status,
    parse_verification_status,
)


@pytest.mark.parametrize("kind", list(ClaimKind))
def test_claim_kind_accepted(kind: ClaimKind) -> None:
    assert parse_claim_kind(kind) is kind
    assert parse_claim_kind(kind.value) is kind


def test_claim_kind_unknown_rejected() -> None:
    with pytest.raises(ClaimRefError):
        parse_claim_kind("soft_skill_graph")


def test_claim_kind_empty_rejected() -> None:
    with pytest.raises(ClaimRefError):
        parse_claim_kind("")
    with pytest.raises(ClaimRefError):
        parse_claim_kind("   ")


def test_no_automatic_fallback_to_other() -> None:
    with pytest.raises(ClaimRefError):
        parse_claim_kind("mystery")
    assert parse_claim_kind("other") is ClaimKind.OTHER


@pytest.mark.parametrize("origin", list(ClaimOrigin))
def test_claim_origin_accepted(origin: ClaimOrigin) -> None:
    assert parse_claim_origin(origin) is origin


@pytest.mark.parametrize("status", list(SupportStatus))
def test_support_status_accepted(status: SupportStatus) -> None:
    assert parse_support_status(status) is status


@pytest.mark.parametrize("status", list(VerificationStatus))
def test_verification_status_accepted(status: VerificationStatus) -> None:
    assert parse_verification_status(status) is status


def test_unknown_statuses_rejected() -> None:
    with pytest.raises(ClaimRefError):
        parse_claim_origin("invented")
    with pytest.raises(ClaimRefError):
        parse_support_status("invented")
    with pytest.raises(ClaimRefError):
        parse_verification_status("invented")


def test_source_linked_does_not_imply_evidence_backed() -> None:
    assert SupportStatus.SOURCE_LINKED is not SupportStatus.EVIDENCE_BACKED
    assert parse_support_status("source_linked") is SupportStatus.SOURCE_LINKED
    assert parse_support_status("source_linked") is not SupportStatus.EVIDENCE_BACKED


def test_evidence_backed_does_not_imply_verified() -> None:
    assert SupportStatus.EVIDENCE_BACKED.value != VerificationStatus.VERIFIED.value
    # Axes are independent enums; linking support does not set verification.
    support = parse_support_status("evidence_backed")
    verification = parse_verification_status("unverified")
    assert support is SupportStatus.EVIDENCE_BACKED
    assert verification is VerificationStatus.UNVERIFIED
