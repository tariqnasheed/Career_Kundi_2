"""
Lifecycle loop service helpers (0050-PF7-S1).

Create/get/list only. No workflow execution, scoring, or automation.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.career_subject import CareerSubject
from app.db.models.lifecycle import (
    CareerAttempt,
    CareerFeedback,
    CareerGoal,
    CareerOutcome,
    CareerRecommendation,
)
from app.db.models.provenance import SourceRecord, SourceSnapshot
from app.platform.identity.refs import ActorRef, ActorType
from app.platform.lifecycle.kinds import (
    parse_attempt_kind,
    parse_feedback_kind,
    parse_goal_kind,
    parse_lifecycle_status,
    parse_outcome_kind,
    parse_recommendation_kind,
)
from app.platform.lifecycle.refs import LifecycleRefError


def _trim_required(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise LifecycleRefError(f"{label} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise LifecycleRefError(f"{label} must not be empty")
    return cleaned


def _trim_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned if cleaned else None


def _actor_fields(
    created_by_actor: ActorRef | None,
) -> tuple[str | None, uuid.UUID | None]:
    if created_by_actor is None:
        return None, None
    if not isinstance(created_by_actor, ActorRef):
        raise LifecycleRefError("created_by_actor must be ActorRef")
    actor_type = (
        created_by_actor.actor_type.value
        if isinstance(created_by_actor.actor_type, ActorType)
        else str(created_by_actor.actor_type)
    )
    return actor_type, uuid.UUID(str(created_by_actor.actor_id))


async def _require_subject(db: AsyncSession, subject_id: uuid.UUID) -> None:
    subject = (
        await db.execute(select(CareerSubject).where(CareerSubject.id == subject_id))
    ).scalar_one_or_none()
    if subject is None:
        raise LifecycleRefError(f"subject does not exist: {subject_id}")


async def create_goal(
    db: AsyncSession,
    *,
    subject_id: uuid.UUID,
    goal_kind: object,
    title: str,
    status: object,
    description: str | None = None,
    created_by_actor: ActorRef | None = None,
) -> CareerGoal:
    await _require_subject(db, subject_id)
    kind = parse_goal_kind(goal_kind)
    st = parse_lifecycle_status(status)
    actor_type, actor_id = _actor_fields(created_by_actor)
    row = CareerGoal(
        subject_id=subject_id,
        goal_kind=kind.value,
        title=_trim_required(title, "title"),
        description=_trim_optional(description),
        status=st.value,
        created_by_actor_type=actor_type,
        created_by_actor_id=actor_id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_goal(
    db: AsyncSession, goal_id: uuid.UUID
) -> CareerGoal | None:
    result = await db.execute(select(CareerGoal).where(CareerGoal.id == goal_id))
    return result.scalar_one_or_none()


async def get_goal_for_subject(
    db: AsyncSession, subject_id: uuid.UUID, goal_id: uuid.UUID
) -> CareerGoal | None:
    """Return goal only when it belongs to subject_id; otherwise None."""
    result = await db.execute(
        select(CareerGoal).where(
            CareerGoal.id == goal_id,
            CareerGoal.subject_id == subject_id,
        )
    )
    return result.scalar_one_or_none()


async def list_subject_goals(
    db: AsyncSession, subject_id: uuid.UUID
) -> list[CareerGoal]:
    result = await db.execute(
        select(CareerGoal)
        .where(CareerGoal.subject_id == subject_id)
        .order_by(CareerGoal.created_at.asc())
    )
    return list(result.scalars().all())


async def create_recommendation(
    db: AsyncSession,
    *,
    subject_id: uuid.UUID,
    recommendation_kind: object,
    title: str,
    status: object,
    goal_id: uuid.UUID | None = None,
    rationale: str | None = None,
    source_id: uuid.UUID | None = None,
    snapshot_id: uuid.UUID | None = None,
    created_by_actor: ActorRef | None = None,
) -> CareerRecommendation:
    await _require_subject(db, subject_id)
    kind = parse_recommendation_kind(recommendation_kind)
    st = parse_lifecycle_status(status)

    if goal_id is not None:
        goal = await get_goal(db, goal_id)
        if goal is None:
            raise LifecycleRefError(f"goal does not exist: {goal_id}")
        if goal.subject_id != subject_id:
            raise LifecycleRefError("goal subject_id does not match recommendation subject_id")

    if snapshot_id is not None and source_id is None:
        raise LifecycleRefError("snapshot_id requires source_id")
    if source_id is not None:
        source = (
            await db.execute(select(SourceRecord).where(SourceRecord.id == source_id))
        ).scalar_one_or_none()
        if source is None:
            raise LifecycleRefError(f"source does not exist: {source_id}")
    if snapshot_id is not None:
        snapshot = (
            await db.execute(
                select(SourceSnapshot).where(SourceSnapshot.id == snapshot_id)
            )
        ).scalar_one_or_none()
        if snapshot is None:
            raise LifecycleRefError(f"snapshot does not exist: {snapshot_id}")
        assert source_id is not None
        if snapshot.source_id != source_id:
            raise LifecycleRefError(
                "snapshot.source_id does not match supplied source_id"
            )

    actor_type, actor_id = _actor_fields(created_by_actor)
    row = CareerRecommendation(
        subject_id=subject_id,
        goal_id=goal_id,
        recommendation_kind=kind.value,
        title=_trim_required(title, "title"),
        rationale=_trim_optional(rationale),
        status=st.value,
        source_id=source_id,
        snapshot_id=snapshot_id,
        created_by_actor_type=actor_type,
        created_by_actor_id=actor_id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_recommendation(
    db: AsyncSession, recommendation_id: uuid.UUID
) -> CareerRecommendation | None:
    result = await db.execute(
        select(CareerRecommendation).where(
            CareerRecommendation.id == recommendation_id
        )
    )
    return result.scalar_one_or_none()


async def list_subject_recommendations(
    db: AsyncSession, subject_id: uuid.UUID
) -> list[CareerRecommendation]:
    result = await db.execute(
        select(CareerRecommendation)
        .where(CareerRecommendation.subject_id == subject_id)
        .order_by(CareerRecommendation.created_at.asc())
    )
    return list(result.scalars().all())


async def create_attempt(
    db: AsyncSession,
    *,
    subject_id: uuid.UUID,
    attempt_kind: object,
    title: str,
    status: object,
    goal_id: uuid.UUID | None = None,
    recommendation_id: uuid.UUID | None = None,
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
    created_by_actor: ActorRef | None = None,
) -> CareerAttempt:
    await _require_subject(db, subject_id)
    kind = parse_attempt_kind(attempt_kind)
    st = parse_lifecycle_status(status)

    if started_at is not None and completed_at is not None and completed_at < started_at:
        raise LifecycleRefError("completed_at cannot be before started_at")

    if goal_id is not None:
        goal = await get_goal(db, goal_id)
        if goal is None:
            raise LifecycleRefError(f"goal does not exist: {goal_id}")
        if goal.subject_id != subject_id:
            raise LifecycleRefError("goal subject_id does not match attempt subject_id")

    if recommendation_id is not None:
        rec = await get_recommendation(db, recommendation_id)
        if rec is None:
            raise LifecycleRefError(
                f"recommendation does not exist: {recommendation_id}"
            )
        if rec.subject_id != subject_id:
            raise LifecycleRefError(
                "recommendation subject_id does not match attempt subject_id"
            )

    actor_type, actor_id = _actor_fields(created_by_actor)
    row = CareerAttempt(
        subject_id=subject_id,
        goal_id=goal_id,
        recommendation_id=recommendation_id,
        attempt_kind=kind.value,
        title=_trim_required(title, "title"),
        status=st.value,
        started_at=started_at,
        completed_at=completed_at,
        created_by_actor_type=actor_type,
        created_by_actor_id=actor_id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_attempt(
    db: AsyncSession, attempt_id: uuid.UUID
) -> CareerAttempt | None:
    result = await db.execute(
        select(CareerAttempt).where(CareerAttempt.id == attempt_id)
    )
    return result.scalar_one_or_none()


async def list_subject_attempts(
    db: AsyncSession, subject_id: uuid.UUID
) -> list[CareerAttempt]:
    result = await db.execute(
        select(CareerAttempt)
        .where(CareerAttempt.subject_id == subject_id)
        .order_by(CareerAttempt.created_at.asc())
    )
    return list(result.scalars().all())


async def create_outcome(
    db: AsyncSession,
    *,
    subject_id: uuid.UUID,
    outcome_kind: object,
    title: str,
    attempt_id: uuid.UUID | None = None,
    description: str | None = None,
    occurred_at: datetime | None = None,
) -> CareerOutcome:
    await _require_subject(db, subject_id)
    kind = parse_outcome_kind(outcome_kind)

    if attempt_id is not None:
        attempt = await get_attempt(db, attempt_id)
        if attempt is None:
            raise LifecycleRefError(f"attempt does not exist: {attempt_id}")
        if attempt.subject_id != subject_id:
            raise LifecycleRefError(
                "attempt subject_id does not match outcome subject_id"
            )

    row = CareerOutcome(
        subject_id=subject_id,
        attempt_id=attempt_id,
        outcome_kind=kind.value,
        title=_trim_required(title, "title"),
        description=_trim_optional(description),
        occurred_at=occurred_at,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_outcome(
    db: AsyncSession, outcome_id: uuid.UUID
) -> CareerOutcome | None:
    result = await db.execute(
        select(CareerOutcome).where(CareerOutcome.id == outcome_id)
    )
    return result.scalar_one_or_none()


async def list_subject_outcomes(
    db: AsyncSession, subject_id: uuid.UUID
) -> list[CareerOutcome]:
    result = await db.execute(
        select(CareerOutcome)
        .where(CareerOutcome.subject_id == subject_id)
        .order_by(CareerOutcome.created_at.asc())
    )
    return list(result.scalars().all())


async def create_feedback(
    db: AsyncSession,
    *,
    subject_id: uuid.UUID,
    feedback_kind: object,
    message: str,
    goal_id: uuid.UUID | None = None,
    recommendation_id: uuid.UUID | None = None,
    attempt_id: uuid.UUID | None = None,
    outcome_id: uuid.UUID | None = None,
    created_by_actor: ActorRef | None = None,
) -> CareerFeedback:
    await _require_subject(db, subject_id)
    kind = parse_feedback_kind(feedback_kind)

    if goal_id is not None:
        goal = await get_goal(db, goal_id)
        if goal is None or goal.subject_id != subject_id:
            raise LifecycleRefError("goal must exist and belong to the same subject")
    if recommendation_id is not None:
        rec = await get_recommendation(db, recommendation_id)
        if rec is None or rec.subject_id != subject_id:
            raise LifecycleRefError(
                "recommendation must exist and belong to the same subject"
            )
    if attempt_id is not None:
        attempt = await get_attempt(db, attempt_id)
        if attempt is None or attempt.subject_id != subject_id:
            raise LifecycleRefError(
                "attempt must exist and belong to the same subject"
            )
    if outcome_id is not None:
        outcome = await get_outcome(db, outcome_id)
        if outcome is None or outcome.subject_id != subject_id:
            raise LifecycleRefError(
                "outcome must exist and belong to the same subject"
            )

    actor_type, actor_id = _actor_fields(created_by_actor)
    row = CareerFeedback(
        subject_id=subject_id,
        goal_id=goal_id,
        recommendation_id=recommendation_id,
        attempt_id=attempt_id,
        outcome_id=outcome_id,
        feedback_kind=kind.value,
        message=_trim_required(message, "message"),
        created_by_actor_type=actor_type,
        created_by_actor_id=actor_id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_feedback(
    db: AsyncSession, feedback_id: uuid.UUID
) -> CareerFeedback | None:
    result = await db.execute(
        select(CareerFeedback).where(CareerFeedback.id == feedback_id)
    )
    return result.scalar_one_or_none()


async def list_subject_feedback(
    db: AsyncSession, subject_id: uuid.UUID
) -> list[CareerFeedback]:
    result = await db.execute(
        select(CareerFeedback)
        .where(CareerFeedback.subject_id == subject_id)
        .order_by(CareerFeedback.created_at.asc())
    )
    return list(result.scalars().all())
