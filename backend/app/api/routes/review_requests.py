"""
Private review-request API (0053-F10).

Authenticated current-user request/list/get/cancel only.
A review request is not verification. No approve/reject/conflict.
Does not mutate claim support_status or verification_status.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.errors import ConflictError, NotFoundError, ValidationFailedError
from app.db.models.claim import ClaimRecord
from app.db.models.review_request import ReviewRequest
from app.db.models.user import User
from app.db.session import get_db
from app.platform.identity.refs import ActorRef, ActorType
from app.platform.kernel import parse_entity_id
from app.platform.verification.display import (
    review_state_help_text,
    review_state_label,
)
from app.platform.verification.refs import VerificationRefError
from app.platform.verification.service import (
    cancel_review_request,
    create_review_request,
    get_review_request_for_owner,
    list_review_requests_for_owner,
)
from app.schemas.review_request import (
    ApiListMeta,
    ReviewRequestCancel,
    ReviewRequestCreate,
    ReviewRequestEnvelope,
    ReviewRequestListEnvelope,
    ReviewRequestRead,
)

router = APIRouter(prefix="/review-requests", tags=["review-requests"])

_REVIEW_REQUEST_WARNING = (
    "A review request is not verification. Claim status changes require a "
    "future explicit review workflow."
)


def _map_error(exc: VerificationRefError) -> Exception:
    message = str(exc)
    lowered = message.lower()
    if "duplicate" in lowered:
        return ConflictError(message)
    if "does not exist" in lowered or "not owned" in lowered:
        if "claim" in lowered:
            return NotFoundError("Claim not found.")
        return NotFoundError("Review request not found.")
    return ValidationFailedError(message)


def _safe_claim_verification_label() -> str:
    return "Not independently verified"


async def _review_request_read(
    db: AsyncSession,
    row: ReviewRequest,
) -> ReviewRequestRead:
    claim = (
        await db.execute(select(ClaimRecord).where(ClaimRecord.id == row.claim_id))
    ).scalar_one_or_none()
    claim_verification_status = (
        claim.verification_status if claim is not None else "unverified"
    )
    return ReviewRequestRead(
        id=row.id,
        subject_id=row.subject_id,
        claim_id=row.claim_id,
        review_state=row.review_state,
        review_state_label=review_state_label(row.review_state),
        review_state_help_text=review_state_help_text(row.review_state),
        reviewer_type=row.reviewer_type,
        request_note=row.request_note,
        cancellation_reason=row.cancellation_reason,
        created_at=row.created_at,
        updated_at=row.updated_at,
        cancelled_at=row.cancelled_at,
        claim_verification_status=claim_verification_status,
        claim_verification_label=_safe_claim_verification_label(),
        warning=_REVIEW_REQUEST_WARNING,
    )


@router.post("", response_model=ReviewRequestEnvelope, status_code=201)
async def create_review_request_api(
    body: ReviewRequestCreate,
    user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> ReviewRequestEnvelope:
    """Request a private review for an owned claim. Not verification."""
    try:
        actor = ActorRef(
            actor_type=ActorType.USER,
            actor_id=parse_entity_id(user.id),
        )
        row = await create_review_request(
            db,
            owner_user_id=user.id,
            claim_id=body.claim_id,
            request_note=body.request_note,
            created_by_actor=actor,
        )
    except VerificationRefError as exc:
        raise _map_error(exc) from exc
    return ReviewRequestEnvelope(data=await _review_request_read(db, row))


@router.get("", response_model=ReviewRequestListEnvelope)
async def list_review_requests_api(
    user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> ReviewRequestListEnvelope:
    """List private review requests owned by the current user."""
    rows = await list_review_requests_for_owner(db, user.id)
    data = [await _review_request_read(db, row) for row in rows]
    return ReviewRequestListEnvelope(data=data, meta=ApiListMeta(count=len(data)))


@router.get("/{request_id}", response_model=ReviewRequestEnvelope)
async def get_review_request_api(
    request_id: uuid.UUID,
    user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> ReviewRequestEnvelope:
    """Get one owned review request (404 if not owned)."""
    row = await get_review_request_for_owner(db, request_id, user.id)
    if row is None:
        raise NotFoundError("Review request not found.")
    return ReviewRequestEnvelope(data=await _review_request_read(db, row))


@router.post(
    "/{request_id}/cancel",
    response_model=ReviewRequestEnvelope,
)
async def cancel_review_request_api(
    request_id: uuid.UUID,
    body: ReviewRequestCancel = ReviewRequestCancel(),  # noqa: B008
    user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> ReviewRequestEnvelope:
    """Cancel an owned requested review. Not verification."""
    try:
        row = await cancel_review_request(
            db,
            request_id=request_id,
            owner_user_id=user.id,
            cancellation_reason=body.cancellation_reason,
        )
    except VerificationRefError as exc:
        raise _map_error(exc) from exc
    return ReviewRequestEnvelope(data=await _review_request_read(db, row))
