"""
Review request service (0053-F10).

Private user request/cancel only. A review request is not verification.
Does not mutate claim support_status or verification_status.
Does not approve/reject/conflict or move to under_review.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.career_subject import CareerSubject
from app.db.models.claim import ClaimRecord
from app.db.models.review_request import ReviewRequest
from app.platform.identity.refs import ActorRef
from app.platform.verification.contracts import validate_review_transition
from app.platform.verification.refs import VerificationRefError
from app.platform.verification.status import ReviewActorType, ReviewState

ACTIVE_REVIEW_STATES: frozenset[str] = frozenset({ReviewState.REQUESTED.value})


def _actor_fields(
    created_by_actor: ActorRef | None,
) -> tuple[str | None, uuid.UUID | None]:
    if created_by_actor is None:
        return None, None
    return created_by_actor.actor_type.value, uuid.UUID(str(created_by_actor.actor_id))


async def _get_owned_claim(
    db: AsyncSession,
    *,
    claim_id: uuid.UUID,
    owner_user_id: uuid.UUID,
) -> ClaimRecord | None:
    claim = (
        await db.execute(select(ClaimRecord).where(ClaimRecord.id == claim_id))
    ).scalar_one_or_none()
    if claim is None:
        return None
    subject = (
        await db.execute(
            select(CareerSubject).where(CareerSubject.id == claim.subject_id)
        )
    ).scalar_one_or_none()
    if subject is None or subject.owner_user_id != owner_user_id:
        return None
    return claim


async def create_review_request(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    claim_id: uuid.UUID,
    request_note: str | None = None,
    created_by_actor: ActorRef | None = None,
) -> ReviewRequest:
    """
    Create a private review request for an owned claim.

    Starts at ReviewState.REQUESTED. Does not mutate claim status axes.
    """
    validate_review_transition(
        ReviewState.NOT_REQUESTED,
        ReviewState.REQUESTED,
        ReviewActorType.USER,
    )

    claim = await _get_owned_claim(
        db, claim_id=claim_id, owner_user_id=owner_user_id
    )
    if claim is None:
        raise VerificationRefError("claim does not exist or is not owned")

    prior_support = claim.support_status
    prior_verification = claim.verification_status

    existing = (
        await db.execute(
            select(ReviewRequest).where(
                ReviewRequest.claim_id == claim_id,
                ReviewRequest.review_state.in_(tuple(ACTIVE_REVIEW_STATES)),
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise VerificationRefError(
            "duplicate active review request for claim is not allowed"
        )

    actor_type, actor_id = _actor_fields(created_by_actor)
    row = ReviewRequest(
        owner_user_id=owner_user_id,
        subject_id=claim.subject_id,
        claim_id=claim.id,
        review_state=ReviewState.REQUESTED.value,
        reviewer_type=None,
        request_note=request_note,
        cancellation_reason=None,
        created_by_actor_type=actor_type,
        created_by_actor_id=actor_id,
        cancelled_at=None,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)

    refreshed_claim = (
        await db.execute(select(ClaimRecord).where(ClaimRecord.id == claim_id))
    ).scalar_one()
    if (
        refreshed_claim.support_status != prior_support
        or refreshed_claim.verification_status != prior_verification
    ):
        raise VerificationRefError(
            "create_review_request must not mutate claim support or verification status"
        )
    return row


async def get_review_request_for_owner(
    db: AsyncSession,
    request_id: uuid.UUID,
    owner_user_id: uuid.UUID,
) -> ReviewRequest | None:
    """Return review request only when owned; else None (safe 404)."""
    row = (
        await db.execute(select(ReviewRequest).where(ReviewRequest.id == request_id))
    ).scalar_one_or_none()
    if row is None or row.owner_user_id != owner_user_id:
        return None
    return row


async def list_review_requests_for_owner(
    db: AsyncSession,
    owner_user_id: uuid.UUID,
) -> list[ReviewRequest]:
    result = await db.execute(
        select(ReviewRequest)
        .where(ReviewRequest.owner_user_id == owner_user_id)
        .order_by(ReviewRequest.created_at.asc())
    )
    return list(result.scalars().all())


async def cancel_review_request(
    db: AsyncSession,
    *,
    request_id: uuid.UUID,
    owner_user_id: uuid.UUID,
    cancellation_reason: str | None = None,
) -> ReviewRequest:
    """
    Cancel an owned review request from requested → cancelled.

    F10 does not cancel under_review (that state is not created by F10 APIs).
    Does not mutate claim status axes.
    """
    row = await get_review_request_for_owner(db, request_id, owner_user_id)
    if row is None:
        raise VerificationRefError("review request does not exist or is not owned")

    if row.review_state != ReviewState.REQUESTED.value:
        raise VerificationRefError(
            f"F10 cancel allows only review_state=requested; got {row.review_state!r}"
        )

    validate_review_transition(
        ReviewState.REQUESTED,
        ReviewState.CANCELLED,
        ReviewActorType.USER,
        reason=cancellation_reason,
    )

    claim = (
        await db.execute(select(ClaimRecord).where(ClaimRecord.id == row.claim_id))
    ).scalar_one()
    prior_support = claim.support_status
    prior_verification = claim.verification_status

    row.review_state = ReviewState.CANCELLED.value
    row.cancellation_reason = cancellation_reason
    row.cancelled_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(row)

    refreshed_claim = (
        await db.execute(select(ClaimRecord).where(ClaimRecord.id == row.claim_id))
    ).scalar_one()
    if (
        refreshed_claim.support_status != prior_support
        or refreshed_claim.verification_status != prior_verification
    ):
        raise VerificationRefError(
            "cancel_review_request must not mutate claim support or verification status"
        )
    return row
