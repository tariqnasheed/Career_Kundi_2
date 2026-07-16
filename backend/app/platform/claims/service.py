"""
Claim service helpers (0050-PF5-S1 / 0053-F1).

Create / get / list only. F1 create-time contract forbids verified /
evidence-backed statuses. No silent status upgrades. No evidence/verification
ownership. No public HTTP routes.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.career_subject import CareerSubject
from app.db.models.claim import ClaimRecord
from app.db.models.provenance import SourceRecord, SourceSnapshot
from app.platform.claims.contracts import validate_claim_create_contract
from app.platform.claims.refs import ClaimRefError
from app.platform.identity.refs import ActorRef, ActorType


def _trim_required(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise ClaimRefError(f"{label} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise ClaimRefError(f"{label} must not be empty")
    return cleaned


async def create_claim(
    db: AsyncSession,
    *,
    subject_id: uuid.UUID,
    claim_kind: object,
    claim_key: str,
    claim_value: str,
    claim_origin: object,
    support_status: object,
    verification_status: object,
    source_id: uuid.UUID | None = None,
    snapshot_id: uuid.UUID | None = None,
    created_by_actor: ActorRef | None = None,
) -> ClaimRecord:
    validated = validate_claim_create_contract(
        claim_kind=claim_kind,
        claim_origin=claim_origin,
        support_status=support_status,
        verification_status=verification_status,
        source_id=source_id,
        snapshot_id=snapshot_id,
    )
    key = _trim_required(claim_key, "claim_key")
    value = _trim_required(claim_value, "claim_value")

    subject = (
        await db.execute(select(CareerSubject).where(CareerSubject.id == subject_id))
    ).scalar_one_or_none()
    if subject is None:
        raise ClaimRefError(f"subject does not exist: {subject_id}")

    if validated.source_id is not None:
        source = (
            await db.execute(
                select(SourceRecord).where(SourceRecord.id == validated.source_id)
            )
        ).scalar_one_or_none()
        if source is None:
            raise ClaimRefError(f"source does not exist: {validated.source_id}")

    if validated.snapshot_id is not None:
        snapshot = (
            await db.execute(
                select(SourceSnapshot).where(
                    SourceSnapshot.id == validated.snapshot_id
                )
            )
        ).scalar_one_or_none()
        if snapshot is None:
            raise ClaimRefError(f"snapshot does not exist: {validated.snapshot_id}")
        assert validated.source_id is not None  # enforced by contract
        if snapshot.source_id != validated.source_id:
            raise ClaimRefError(
                "snapshot.source_id does not match supplied source_id"
            )

    actor_type: str | None = None
    actor_id: uuid.UUID | None = None
    if created_by_actor is not None:
        if not isinstance(created_by_actor, ActorRef):
            raise ClaimRefError("created_by_actor must be ActorRef")
        actor_type = (
            created_by_actor.actor_type.value
            if isinstance(created_by_actor.actor_type, ActorType)
            else str(created_by_actor.actor_type)
        )
        actor_id = uuid.UUID(str(created_by_actor.actor_id))

    row = ClaimRecord(
        subject_id=subject_id,
        claim_kind=validated.claim_kind.value,
        claim_key=key,
        claim_value=value,
        claim_origin=validated.claim_origin.value,
        support_status=validated.support_status.value,
        verification_status=validated.verification_status.value,
        source_id=validated.source_id,
        snapshot_id=validated.snapshot_id,
        created_by_actor_type=actor_type,
        created_by_actor_id=actor_id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_claim(
    db: AsyncSession, claim_id: uuid.UUID
) -> ClaimRecord | None:
    result = await db.execute(select(ClaimRecord).where(ClaimRecord.id == claim_id))
    return result.scalar_one_or_none()


async def list_subject_claims(
    db: AsyncSession, subject_id: uuid.UUID
) -> list[ClaimRecord]:
    result = await db.execute(
        select(ClaimRecord)
        .where(ClaimRecord.subject_id == subject_id)
        .order_by(ClaimRecord.created_at.asc())
    )
    return list(result.scalars().all())
