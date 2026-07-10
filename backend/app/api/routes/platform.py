"""
Platform API foundation (0050-PF8-S1).

Subjects + subject-scoped goals with consistent response envelopes.
No public CRUD for claims/provenance/geo/lifecycle write surfaces.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.errors import NotFoundError, ValidationFailedError
from app.db.models.user import User
from app.db.session import get_db
from app.platform.identity.refs import ActorRef, ActorType
from app.platform.identity.service import (
    create_subject_for_user,
    ensure_owned_subject,
    list_subjects_for_user,
)
from app.platform.kernel import parse_entity_id
from app.platform.lifecycle.refs import LifecycleRefError
from app.platform.lifecycle.service import (
    create_goal,
    get_goal_for_subject,
    list_subject_goals,
)
from app.schemas.platform import (
    ApiListMeta,
    GoalCreate,
    GoalEnvelope,
    GoalListEnvelope,
    GoalRead,
    SubjectEnvelope,
    SubjectListEnvelope,
    SubjectRead,
)

router = APIRouter(prefix="/platform", tags=["platform"])


def _subject_read(subject) -> SubjectRead:
    return SubjectRead.model_validate(subject)


def _goal_read(goal) -> GoalRead:
    return GoalRead.model_validate(goal)


@router.post("/subjects", response_model=SubjectEnvelope, status_code=201)
async def create_career_subject(
    user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SubjectEnvelope:
    """Create a new CareerSubject owned by the authenticated user."""
    subject = await create_subject_for_user(db, user.id)
    return SubjectEnvelope(data=_subject_read(subject))


@router.get("/subjects", response_model=SubjectListEnvelope)
async def list_career_subjects(
    user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SubjectListEnvelope:
    """List subjects owned by the current user. Does not auto-create."""
    subjects = await list_subjects_for_user(db, user.id)
    data = [_subject_read(s) for s in subjects]
    return SubjectListEnvelope(data=data, meta=ApiListMeta(count=len(data)))


@router.get("/subjects/{subject_id}", response_model=SubjectEnvelope)
async def get_career_subject(
    subject_id: uuid.UUID,
    user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SubjectEnvelope:
    """Read a subject owned by the current user (404 if not owned)."""
    subject = await ensure_owned_subject(db, subject_id, user.id)
    if subject is None:
        raise NotFoundError("Career subject not found.")
    return SubjectEnvelope(data=_subject_read(subject))


@router.post(
    "/subjects/{subject_id}/goals",
    response_model=GoalEnvelope,
    status_code=201,
)
async def create_subject_goal(
    subject_id: uuid.UUID,
    body: GoalCreate,
    user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> GoalEnvelope:
    """Create a goal under an owned subject."""
    subject = await ensure_owned_subject(db, subject_id, user.id)
    if subject is None:
        raise NotFoundError("Career subject not found.")
    try:
        actor = ActorRef(
            actor_type=ActorType.USER,
            actor_id=parse_entity_id(user.id),
        )
        goal = await create_goal(
            db,
            subject_id=subject.id,
            goal_kind=body.goal_kind,
            title=body.title,
            description=body.description,
            status=body.status,
            created_by_actor=actor,
        )
    except LifecycleRefError as exc:
        raise ValidationFailedError(str(exc)) from exc
    return GoalEnvelope(data=_goal_read(goal))


@router.get(
    "/subjects/{subject_id}/goals",
    response_model=GoalListEnvelope,
)
async def list_subject_goals_api(
    subject_id: uuid.UUID,
    user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> GoalListEnvelope:
    """List goals for an owned subject."""
    subject = await ensure_owned_subject(db, subject_id, user.id)
    if subject is None:
        raise NotFoundError("Career subject not found.")
    goals = await list_subject_goals(db, subject.id)
    data = [_goal_read(g) for g in goals]
    return GoalListEnvelope(data=data, meta=ApiListMeta(count=len(data)))


@router.get(
    "/subjects/{subject_id}/goals/{goal_id}",
    response_model=GoalEnvelope,
)
async def get_subject_goal(
    subject_id: uuid.UUID,
    goal_id: uuid.UUID,
    user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> GoalEnvelope:
    """Read a goal under an owned subject (404 if missing or mismatched)."""
    subject = await ensure_owned_subject(db, subject_id, user.id)
    if subject is None:
        raise NotFoundError("Career subject not found.")
    goal = await get_goal_for_subject(db, subject.id, goal_id)
    if goal is None:
        raise NotFoundError("Career goal not found.")
    return GoalEnvelope(data=_goal_read(goal))
