"""
0053-F9 review/verification state-machine contracts.

Pure domain validation — no FastAPI, SQLAlchemy, DB writes, or claim mutation.
Upload/link/source never verify. Claim verification_status changes require an
explicit future review service that is not implemented in F9.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.platform.claims.status import (
    VerificationStatus,
    parse_verification_status,
)
from app.platform.verification.refs import VerificationRefError
from app.platform.verification.status import (
    ReviewActorType,
    ReviewState,
    parse_review_actor_type,
    parse_review_state,
)

# (from_state, to_state) -> actors allowed to perform the transition.
_ALLOWED_TRANSITIONS: dict[
    tuple[ReviewState, ReviewState], frozenset[ReviewActorType]
] = {
    (ReviewState.NOT_REQUESTED, ReviewState.REQUESTED): frozenset(
        {ReviewActorType.USER}
    ),
    (ReviewState.REQUESTED, ReviewState.UNDER_REVIEW): frozenset(
        {ReviewActorType.REVIEWER}
    ),
    (ReviewState.UNDER_REVIEW, ReviewState.NEEDS_MORE_EVIDENCE): frozenset(
        {ReviewActorType.REVIEWER}
    ),
    (ReviewState.NEEDS_MORE_EVIDENCE, ReviewState.UNDER_REVIEW): frozenset(
        {ReviewActorType.REVIEWER}
    ),
    (ReviewState.UNDER_REVIEW, ReviewState.APPROVED): frozenset(
        {ReviewActorType.APPROVER}
    ),
    (ReviewState.UNDER_REVIEW, ReviewState.REJECTED): frozenset(
        {ReviewActorType.REVIEWER, ReviewActorType.APPROVER}
    ),
    (ReviewState.UNDER_REVIEW, ReviewState.CONFLICTED): frozenset(
        {ReviewActorType.REVIEWER, ReviewActorType.APPROVER}
    ),
    (ReviewState.REQUESTED, ReviewState.CANCELLED): frozenset(
        {ReviewActorType.USER}
    ),
    (ReviewState.UNDER_REVIEW, ReviewState.CANCELLED): frozenset(
        {ReviewActorType.USER}
    ),
    (ReviewState.APPROVED, ReviewState.EXPIRED): frozenset(
        {ReviewActorType.SYSTEM_POLICY}
    ),
}

# Review outcomes that may map to claim VerificationStatus in a future service.
_OUTCOME_TO_CLAIM_VERIFICATION: dict[ReviewState, VerificationStatus] = {
    ReviewState.APPROVED: VerificationStatus.VERIFIED,
    ReviewState.REJECTED: VerificationStatus.REJECTED,
    ReviewState.CONFLICTED: VerificationStatus.CONFLICTING,
}


@dataclass(frozen=True, slots=True)
class ValidatedReviewTransition:
    from_state: ReviewState
    to_state: ReviewState
    actor_type: ReviewActorType
    reason: str | None


def validate_review_transition(
    from_state: object,
    to_state: object,
    actor_type: object,
    reason: str | None = None,
) -> ValidatedReviewTransition:
    """
    Validate a review-state transition for a future review service.

    Does not write to the database or mutate ClaimRecord.
    """
    current = parse_review_state(from_state)
    target = parse_review_state(to_state)
    actor = parse_review_actor_type(actor_type)

    if current == target:
        raise VerificationRefError(
            f"review transition is a no-op: {current.value!r} -> {target.value!r}"
        )

    allowed_actors = _ALLOWED_TRANSITIONS.get((current, target))
    if allowed_actors is None:
        raise VerificationRefError(
            f"forbidden review transition: {current.value!r} -> {target.value!r}"
        )
    if actor not in allowed_actors:
        raise VerificationRefError(
            f"actor {actor.value!r} cannot transition "
            f"{current.value!r} -> {target.value!r}"
        )

    if target == ReviewState.APPROVED and actor != ReviewActorType.APPROVER:
        raise VerificationRefError("only approver may approve a review")

    return ValidatedReviewTransition(
        from_state=current,
        to_state=target,
        actor_type=actor,
        reason=reason,
    )


def map_review_outcome_to_claim_verification_status(
    review_state: object,
) -> VerificationStatus | None:
    """
    Explicit future mapping only. Returns None when claim status must not change.

    F9 does not call this from any API or mutate ClaimRecord.
    """
    state = parse_review_state(review_state)
    return _OUTCOME_TO_CLAIM_VERIFICATION.get(state)


def assert_upload_does_not_verify(
    *,
    resulting_claim_verification_status: object = VerificationStatus.UNVERIFIED,
) -> None:
    """Evidence file upload must leave claim verification unverified."""
    status = parse_verification_status(resulting_claim_verification_status)
    if status != VerificationStatus.UNVERIFIED:
        raise VerificationRefError(
            "evidence upload must not change claim verification_status; "
            f"got {status.value!r}"
        )


def assert_link_does_not_verify(
    *,
    resulting_claim_verification_status: object = VerificationStatus.UNVERIFIED,
) -> None:
    """Evidence-to-claim linking must leave claim verification unverified."""
    status = parse_verification_status(resulting_claim_verification_status)
    if status != VerificationStatus.UNVERIFIED:
        raise VerificationRefError(
            "evidence link must not change claim verification_status; "
            f"got {status.value!r}"
        )


def assert_source_does_not_verify(
    *,
    resulting_claim_verification_status: object = VerificationStatus.UNVERIFIED,
) -> None:
    """Source/snapshot provenance must leave claim verification unverified."""
    status = parse_verification_status(resulting_claim_verification_status)
    if status != VerificationStatus.UNVERIFIED:
        raise VerificationRefError(
            "source/snapshot provenance must not change claim verification_status; "
            f"got {status.value!r}"
        )


def assert_claim_verification_change_requires_review(
    *,
    from_status: object,
    to_status: object,
    review_state: object | None = None,
) -> None:
    """
    Claim verification_status may only change via an explicit future review outcome.

    F9 has no review service that performs this change.
    """
    current = parse_verification_status(from_status)
    target = parse_verification_status(to_status)
    if current == target:
        return

    if target == VerificationStatus.UNVERIFIED:
        # Downgrade / default remains allowed as a future policy concern; F9
        # only blocks upgrades to terminal verified outcomes without review.
        return

    if review_state is None:
        raise VerificationRefError(
            "claim verification_status change requires an explicit review outcome "
            f"({current.value!r} -> {target.value!r})"
        )

    state = parse_review_state(review_state)
    mapped = map_review_outcome_to_claim_verification_status(state)
    if mapped is None:
        raise VerificationRefError(
            f"review_state={state.value!r} must not change claim verification_status"
        )
    if mapped != target:
        raise VerificationRefError(
            f"review_state={state.value!r} maps to {mapped.value!r}, "
            f"not {target.value!r}"
        )


def allowed_review_transitions() -> frozenset[tuple[str, str]]:
    """Exported for docs/tests."""
    return frozenset(
        (frm.value, to.value) for (frm, to) in _ALLOWED_TRANSITIONS
    )
