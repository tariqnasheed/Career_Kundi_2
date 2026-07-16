"""0053-F9 safe review display-language contracts."""

from __future__ import annotations

from app.platform.verification.display import (
    all_review_state_labels,
    can_display_verified_label,
    forbidden_review_label_terms,
    review_state_help_text,
    review_state_label,
    verification_policy_warning,
)
from app.platform.verification.status import ReviewState


def test_safe_labels_for_all_review_states() -> None:
    expected = {
        ReviewState.NOT_REQUESTED: "Not requested",
        ReviewState.REQUESTED: "Review requested",
        ReviewState.UNDER_REVIEW: "Under review",
        ReviewState.NEEDS_MORE_EVIDENCE: "More evidence needed",
        ReviewState.APPROVED: "Approved by review",
        ReviewState.REJECTED: "Rejected by review",
        ReviewState.CONFLICTED: "Conflicting information",
        ReviewState.CANCELLED: "Review cancelled",
        ReviewState.EXPIRED: "Review expired",
    }
    for state, label in expected.items():
        assert review_state_label(state) == label
        help_text = review_state_help_text(state)
        assert help_text
        _assert_safe_blob(help_text)


def test_labels_forbid_unsafe_trust_wording() -> None:
    blob = " ".join(all_review_state_labels()).lower()
    for term in forbidden_review_label_terms():
        assert term not in blob
    assert "verified" not in blob


def test_policy_warning_is_safe_and_explicit() -> None:
    warning = verification_policy_warning()
    assert "do not independently verify" in warning.lower()
    assert "future explicit review workflow" in warning.lower()
    _assert_safe_blob(warning)


def test_can_display_verified_label_only_for_approved() -> None:
    assert can_display_verified_label("approved") is True
    for state in ReviewState:
        if state == ReviewState.APPROVED:
            continue
        assert can_display_verified_label(state) is False


def _assert_safe_blob(text: str) -> None:
    lowered = text.lower()
    for term in (
        "official",
        "trusted",
        "proof of truth",
        "verified credential",
        "verified document",
        "public credential",
        "wallet",
        "blockchain",
        "did",
        "ai verified",
        "self verified",
    ):
        assert term not in lowered
