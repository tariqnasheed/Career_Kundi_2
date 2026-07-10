"""
Privacy service helpers (0050-PF9-S1).

Create/get/list only. No inferred consent. No deletion automation.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.career_subject import CareerSubject
from app.db.models.privacy import ConsentRecord, PrivacyPolicy, RetentionPolicy
from app.platform.identity.refs import ActorRef, ActorType
from app.platform.privacy.kinds import (
    ConsentStatus,
    RetentionCategory,
    parse_consent_status,
    parse_data_classification,
    parse_processing_purpose,
    parse_retention_category,
    parse_visibility_scope,
)
from app.platform.privacy.refs import PrivacyRefError


def _trim_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned if cleaned else None


def _actor_fields(
    actor: ActorRef | None,
) -> tuple[str | None, uuid.UUID | None]:
    if actor is None:
        return None, None
    if not isinstance(actor, ActorRef):
        raise PrivacyRefError("actor must be ActorRef")
    actor_type = (
        actor.actor_type.value
        if isinstance(actor.actor_type, ActorType)
        else str(actor.actor_type)
    )
    return actor_type, uuid.UUID(str(actor.actor_id))


async def _require_subject(db: AsyncSession, subject_id: uuid.UUID) -> None:
    subject = (
        await db.execute(select(CareerSubject).where(CareerSubject.id == subject_id))
    ).scalar_one_or_none()
    if subject is None:
        raise PrivacyRefError(f"subject does not exist: {subject_id}")


async def create_privacy_policy(
    db: AsyncSession,
    *,
    data_classification: object,
    visibility_scope: object,
    processing_purpose: object,
    subject_id: uuid.UUID | None = None,
    description: str | None = None,
    created_by_actor: ActorRef | None = None,
) -> PrivacyPolicy:
    if subject_id is not None:
        await _require_subject(db, subject_id)
    classification = parse_data_classification(data_classification)
    visibility = parse_visibility_scope(visibility_scope)
    purpose = parse_processing_purpose(processing_purpose)
    actor_type, actor_id = _actor_fields(created_by_actor)
    row = PrivacyPolicy(
        subject_id=subject_id,
        data_classification=classification.value,
        visibility_scope=visibility.value,
        processing_purpose=purpose.value,
        description=_trim_optional(description),
        created_by_actor_type=actor_type,
        created_by_actor_id=actor_id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_privacy_policy(
    db: AsyncSession, privacy_policy_id: uuid.UUID
) -> PrivacyPolicy | None:
    result = await db.execute(
        select(PrivacyPolicy).where(PrivacyPolicy.id == privacy_policy_id)
    )
    return result.scalar_one_or_none()


async def list_subject_privacy_policies(
    db: AsyncSession, subject_id: uuid.UUID
) -> list[PrivacyPolicy]:
    result = await db.execute(
        select(PrivacyPolicy)
        .where(PrivacyPolicy.subject_id == subject_id)
        .order_by(PrivacyPolicy.created_at.asc())
    )
    return list(result.scalars().all())


async def create_consent_record(
    db: AsyncSession,
    *,
    subject_id: uuid.UUID,
    processing_purpose: object,
    consent_status: object,
    granted_by_actor: ActorRef | None = None,
    withdrawn_at: datetime | None = None,
    expires_at: datetime | None = None,
) -> ConsentRecord:
    await _require_subject(db, subject_id)
    purpose = parse_processing_purpose(processing_purpose)
    status = parse_consent_status(consent_status)
    if status is ConsentStatus.WITHDRAWN:
        if withdrawn_at is None:
            raise PrivacyRefError("withdrawn status requires withdrawn_at")
    elif withdrawn_at is not None:
        raise PrivacyRefError("withdrawn_at is only allowed when status is withdrawn")
    actor_type, actor_id = _actor_fields(granted_by_actor)
    row = ConsentRecord(
        subject_id=subject_id,
        processing_purpose=purpose.value,
        consent_status=status.value,
        granted_by_actor_type=actor_type,
        granted_by_actor_id=actor_id,
        withdrawn_at=withdrawn_at,
        expires_at=expires_at,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_consent_record(
    db: AsyncSession, consent_record_id: uuid.UUID
) -> ConsentRecord | None:
    result = await db.execute(
        select(ConsentRecord).where(ConsentRecord.id == consent_record_id)
    )
    return result.scalar_one_or_none()


async def list_subject_consent_records(
    db: AsyncSession, subject_id: uuid.UUID
) -> list[ConsentRecord]:
    result = await db.execute(
        select(ConsentRecord)
        .where(ConsentRecord.subject_id == subject_id)
        .order_by(ConsentRecord.created_at.asc())
    )
    return list(result.scalars().all())


async def create_retention_policy(
    db: AsyncSession,
    *,
    retention_category: object,
    subject_id: uuid.UUID | None = None,
    processing_purpose: object | None = None,
    retain_until: datetime | None = None,
    description: str | None = None,
    created_by_actor: ActorRef | None = None,
) -> RetentionPolicy:
    if subject_id is not None:
        await _require_subject(db, subject_id)
    category = parse_retention_category(retention_category)
    if category is RetentionCategory.FIXED_PERIOD and retain_until is None:
        raise PrivacyRefError("fixed_period requires retain_until")
    purpose_value: str | None = None
    if processing_purpose is not None:
        purpose_value = parse_processing_purpose(processing_purpose).value
    actor_type, actor_id = _actor_fields(created_by_actor)
    row = RetentionPolicy(
        subject_id=subject_id,
        retention_category=category.value,
        processing_purpose=purpose_value,
        retain_until=retain_until,
        description=_trim_optional(description),
        created_by_actor_type=actor_type,
        created_by_actor_id=actor_id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_retention_policy(
    db: AsyncSession, retention_policy_id: uuid.UUID
) -> RetentionPolicy | None:
    result = await db.execute(
        select(RetentionPolicy).where(RetentionPolicy.id == retention_policy_id)
    )
    return result.scalar_one_or_none()


async def list_subject_retention_policies(
    db: AsyncSession, subject_id: uuid.UUID
) -> list[RetentionPolicy]:
    result = await db.execute(
        select(RetentionPolicy)
        .where(RetentionPolicy.subject_id == subject_id)
        .order_by(RetentionPolicy.created_at.asc())
    )
    return list(result.scalars().all())
