"""0053-F9 review state-machine transition and mapping contracts."""

from __future__ import annotations

import pytest

from app.platform.claims.status import VerificationStatus
from app.platform.verification.contracts import (
    assert_claim_verification_change_requires_review,
    assert_link_does_not_verify,
    assert_source_does_not_verify,
    assert_upload_does_not_verify,
    map_review_outcome_to_claim_verification_status,
    validate_review_transition,
)
from app.platform.verification.refs import VerificationRefError
from app.platform.verification.status import ReviewActorType, ReviewState


@pytest.mark.parametrize(
    ("frm", "to", "actor"),
    [
        ("not_requested", "requested", "user"),
        ("requested", "under_review", "reviewer"),
        ("under_review", "needs_more_evidence", "reviewer"),
        ("needs_more_evidence", "under_review", "reviewer"),
        ("under_review", "approved", "approver"),
        ("under_review", "rejected", "reviewer"),
        ("under_review", "conflicted", "reviewer"),
        ("requested", "cancelled", "user"),
        ("under_review", "cancelled", "user"),
        ("approved", "expired", "system_policy"),
    ],
)
def test_allowed_transitions_pass(frm: str, to: str, actor: str) -> None:
    result = validate_review_transition(frm, to, actor)
    assert result.from_state.value == frm
    assert result.to_state.value == to
    assert result.actor_type.value == actor


@pytest.mark.parametrize(
    ("frm", "to", "actor"),
    [
        ("not_requested", "approved", "approver"),
        ("requested", "approved", "approver"),
        ("needs_more_evidence", "approved", "approver"),
        ("cancelled", "approved", "approver"),
        ("expired", "approved", "approver"),
        ("approved", "rejected", "reviewer"),
        ("rejected", "approved", "approver"),
        ("not_requested", "requested", "reviewer"),
        ("under_review", "approved", "user"),
        ("under_review", "approved", "reviewer"),
        ("requested", "under_review", "user"),
        ("approved", "expired", "user"),
    ],
)
def test_forbidden_transitions_fail(frm: str, to: str, actor: str) -> None:
    with pytest.raises(VerificationRefError):
        validate_review_transition(frm, to, actor)


def test_user_cannot_approve() -> None:
    with pytest.raises(VerificationRefError):
        validate_review_transition(
            ReviewState.UNDER_REVIEW,
            ReviewState.APPROVED,
            ReviewActorType.USER,
        )


def test_reviewer_cannot_approve() -> None:
    with pytest.raises(VerificationRefError):
        validate_review_transition(
            ReviewState.UNDER_REVIEW,
            ReviewState.APPROVED,
            ReviewActorType.REVIEWER,
        )


def test_non_review_states_cannot_approve() -> None:
    for bogus in ("evidence_linked", "uploaded", "source_linked", "verified"):
        with pytest.raises(VerificationRefError):
            validate_review_transition("not_requested", bogus, "approver")
        with pytest.raises(VerificationRefError):
            validate_review_transition(bogus, "approved", "approver")


def test_forbidden_actor_labels_rejected() -> None:
    for label in (
        "self_verified",
        "user_verified",
        "ai_verified",
        "blockchain_verified",
        "auto_verified",
    ):
        with pytest.raises(VerificationRefError):
            validate_review_transition("under_review", "approved", label)


def test_upload_link_source_do_not_verify() -> None:
    assert_upload_does_not_verify()
    assert_link_does_not_verify()
    assert_source_does_not_verify()
    with pytest.raises(VerificationRefError):
        assert_upload_does_not_verify(
            resulting_claim_verification_status=VerificationStatus.VERIFIED
        )
    with pytest.raises(VerificationRefError):
        assert_link_does_not_verify(
            resulting_claim_verification_status="verified"
        )
    with pytest.raises(VerificationRefError):
        assert_source_does_not_verify(
            resulting_claim_verification_status="verified"
        )


def test_claim_verification_change_requires_explicit_review() -> None:
    with pytest.raises(VerificationRefError):
        assert_claim_verification_change_requires_review(
            from_status="unverified",
            to_status="verified",
            review_state=None,
        )
    with pytest.raises(VerificationRefError):
        assert_claim_verification_change_requires_review(
            from_status="unverified",
            to_status="verified",
            review_state="under_review",
        )
    assert_claim_verification_change_requires_review(
        from_status="unverified",
        to_status="verified",
        review_state="approved",
    )
    assert_claim_verification_change_requires_review(
        from_status="unverified",
        to_status="rejected",
        review_state="rejected",
    )
    assert_claim_verification_change_requires_review(
        from_status="unverified",
        to_status="conflicting",
        review_state="conflicted",
    )


def test_outcome_mapping_is_explicit_and_not_automatic() -> None:
    assert (
        map_review_outcome_to_claim_verification_status("approved")
        == VerificationStatus.VERIFIED
    )
    assert (
        map_review_outcome_to_claim_verification_status("rejected")
        == VerificationStatus.REJECTED
    )
    assert (
        map_review_outcome_to_claim_verification_status("conflicted")
        == VerificationStatus.CONFLICTING
    )
    for state in (
        "not_requested",
        "requested",
        "under_review",
        "needs_more_evidence",
        "cancelled",
        "expired",
    ):
        assert map_review_outcome_to_claim_verification_status(state) is None
