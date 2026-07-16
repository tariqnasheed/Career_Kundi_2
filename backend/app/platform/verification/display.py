"""
0053-F9 safe display labels for review states.

Domain-only helpers for a future review UI. F9 does not expose verification UI.
"""

from __future__ import annotations

from app.platform.verification.refs import VerificationRefError
from app.platform.verification.status import ReviewState, parse_review_state

_FORBIDDEN_LABEL_TERMS = (
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
)

_REVIEW_STATE_LABELS: dict[ReviewState, str] = {
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

_REVIEW_STATE_HELP: dict[ReviewState, str] = {
    ReviewState.NOT_REQUESTED: (
        "No review has been requested. Evidence links do not start a review."
    ),
    ReviewState.REQUESTED: (
        "A review was requested. This does not independently verify the claim."
    ),
    ReviewState.UNDER_REVIEW: (
        "A reviewer is examining the request. The claim remains not independently verified."
    ),
    ReviewState.NEEDS_MORE_EVIDENCE: (
        "More private evidence is needed before review can continue."
    ),
    ReviewState.APPROVED: (
        "A future explicit review approved this outcome. Display only after a real review service exists."
    ),
    ReviewState.REJECTED: (
        "A future explicit review rejected this outcome."
    ),
    ReviewState.CONFLICTED: (
        "Review found conflicting information. This is not independent verification of truth."
    ),
    ReviewState.CANCELLED: "The review request was cancelled.",
    ReviewState.EXPIRED: "A prior approved review outcome has expired.",
}


def review_state_label(value: object) -> str:
    state = parse_review_state(value)
    label = _REVIEW_STATE_LABELS[state]
    _assert_safe_label(label)
    return label


def review_state_help_text(value: object) -> str:
    state = parse_review_state(value)
    text = _REVIEW_STATE_HELP[state]
    _assert_safe_label(text)
    return text


def verification_policy_warning() -> str:
    return (
        "Evidence, file upload, or source links do not independently verify a claim. "
        "Verification requires a future explicit review workflow."
    )


def can_display_verified_label(review_state: object) -> bool:
    """
    True only for an approved review outcome.

    F9 has no UI that shows a Verified badge. Future UI must still avoid
    “Verified Passport” / public trust overclaim.
    """
    return parse_review_state(review_state) == ReviewState.APPROVED


def all_review_state_labels() -> list[str]:
    return [_REVIEW_STATE_LABELS[s] for s in ReviewState]


def forbidden_review_label_terms() -> tuple[str, ...]:
    return _FORBIDDEN_LABEL_TERMS


def _assert_safe_label(text: str) -> None:
    lowered = text.lower()
    for term in _FORBIDDEN_LABEL_TERMS:
        if term in lowered:
            raise VerificationRefError(
                f"unsafe review display wording contains {term!r}: {text!r}"
            )
    # Bare "verified" only allowed inside safe phrases used by policy warning helpers.
    if "verified" in lowered and "not independently verified" not in lowered:
        # Labels intentionally avoid the word verified (use Approved by review).
        raise VerificationRefError(
            f"unsafe review display wording contains bare verified: {text!r}"
        )
