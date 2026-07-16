"""0053-F1 safe display-language mapping tests."""

from __future__ import annotations

from app.platform.claims import SupportStatus, VerificationStatus
from app.platform.claims.display import (
    claim_display_state,
    claim_truth_warning,
    forbidden_support_label_terms,
    support_status_label,
    verification_status_label,
)


def test_source_linked_label_not_verified() -> None:
    label = support_status_label(SupportStatus.SOURCE_LINKED)
    assert label == "Source-linked"
    assert "verified" not in label.lower()


def test_profile_supported_label_not_verified() -> None:
    label = support_status_label(SupportStatus.PROFILE_SUPPORTED)
    assert label == "Profile-backed"
    assert "verified" not in label.lower()


def test_evidence_backed_label_is_evidence_linked_not_proof() -> None:
    label = support_status_label(SupportStatus.EVIDENCE_BACKED)
    assert label == "Evidence-linked"
    assert "verified" not in label.lower()
    assert "truth" not in label.lower()
    assert "official" not in label.lower()
    assert "proof" not in label.lower()


def test_verified_label_only_from_verification_status() -> None:
    assert verification_status_label(VerificationStatus.VERIFIED) == "Verified"
    # Support axis must never produce "Verified"
    for status in SupportStatus:
        assert support_status_label(status) != "Verified"
        assert "verified" not in support_status_label(status).lower()


def test_unverified_label() -> None:
    assert (
        verification_status_label(VerificationStatus.UNVERIFIED)
        == "Not independently verified"
    )


def test_forbidden_terms_absent_from_all_support_labels() -> None:
    forbidden = forbidden_support_label_terms()
    for status in SupportStatus:
        label = support_status_label(status).lower()
        for term in forbidden:
            assert term not in label, f"{status} label contains {term!r}: {label}"


def test_claim_truth_warning_mentions_non_verification() -> None:
    warning = claim_truth_warning()
    assert "not verification" in warning.lower()
    assert "not independently verified" in warning.lower()
    assert "official" not in warning.lower()
    assert "blockchain" not in warning.lower()


def test_claim_display_state_source_linked() -> None:
    state = claim_display_state(
        support_status=SupportStatus.SOURCE_LINKED,
        verification_status=VerificationStatus.UNVERIFIED,
        source_id="source-1",
        snapshot_id=None,
    )
    assert state["support_label"] == "Source-linked"
    assert state["verification_label"] == "Not independently verified"
    assert state["has_source_link"] is True
    assert state["is_independently_verified"] is False
    assert "verified" not in state["support_label"].lower()
