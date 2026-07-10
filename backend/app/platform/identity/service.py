"""
Identity subject service helpers (0050-PF3-S1 / PF8-S1).

Keeps ownership queries out of route handlers.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.career_subject import CareerSubject


async def create_subject_for_user(
    db: AsyncSession, user_id: uuid.UUID
) -> CareerSubject:
    subject = CareerSubject(owner_user_id=user_id)
    db.add(subject)
    await db.commit()
    await db.refresh(subject)
    return subject


async def get_owned_subject(
    db: AsyncSession, subject_id: uuid.UUID, user_id: uuid.UUID
) -> CareerSubject | None:
    """Return subject only when owned by user_id; otherwise None (non-disclosing)."""
    result = await db.execute(
        select(CareerSubject).where(
            CareerSubject.id == subject_id,
            CareerSubject.owner_user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def ensure_owned_subject(
    db: AsyncSession, subject_id: uuid.UUID, user_id: uuid.UUID
) -> CareerSubject | None:
    """Alias for ownership-scoped subject lookup (None → caller maps to 404)."""
    return await get_owned_subject(db, subject_id, user_id)


async def list_subjects_for_user(
    db: AsyncSession, user_id: uuid.UUID
) -> list[CareerSubject]:
    """List CareerSubjects owned by user_id. Does not auto-create."""
    result = await db.execute(
        select(CareerSubject)
        .where(CareerSubject.owner_user_id == user_id)
        .order_by(CareerSubject.created_at.asc())
    )
    return list(result.scalars().all())
