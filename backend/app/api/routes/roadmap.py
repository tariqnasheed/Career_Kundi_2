"""
api/routes/roadmap.py
===========================
Career Roadmap (§4.5) endpoints.

Thin HTTP wrapper around `app.agents.roadmap.graph`'s two pipelines plus
straightforward ORM persistence. No agent logic, prompting, RAG, GraphRAG
traversal, or verification happens in this file — see `app/agents/roadmap/`
for all of that.

Endpoint summary
----------------
POST   /api/v1/roadmap/generate                               — Generate a new roadmap for a target role.
GET    /api/v1/roadmap/                                        — List the current user's roadmaps.
GET    /api/v1/roadmap/{roadmap_id}                            — Fetch one roadmap (with milestones/skills).
DELETE /api/v1/roadmap/{roadmap_id}                            — Delete a roadmap.
POST   /api/v1/roadmap/{roadmap_id}/regenerate                 — Re-run generation in place (new pace/inputs).
PATCH  /api/v1/roadmap/{roadmap_id}/skills/{skill_id}/status   — Mark a skill not_started/in_progress/completed.
POST   /api/v1/roadmap/{roadmap_id}/skills/{skill_id}/refresh  — Regenerate one skill's resources/content.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.roadmap.graph import run_roadmap_generation_pipeline, run_skill_refresh_pipeline
from app.api.deps import get_current_user
from app.api.routes.profile import _get_or_create_profile
from app.core.errors import NotFoundError
from app.db.models.roadmap import Roadmap, RoadmapMilestone, RoadmapSkill
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.roadmap import RoadmapGenerateRequest, RoadmapRead, RoadmapSkillRead, RoadmapSkillStatusUpdate

router = APIRouter(prefix="/roadmap", tags=["roadmap"])


async def _get_owned_roadmap(db: AsyncSession, user: User, roadmap_id: uuid.UUID) -> Roadmap:
    """Fetch a `Roadmap` the current user actually owns, with milestones/skills eager-loaded, or raise `NotFoundError` (never leaks existence of other users' rows)."""
    result = await db.execute(
        select(Roadmap)
        .where(Roadmap.id == roadmap_id, Roadmap.user_id == user.id)
        .options(selectinload(Roadmap.milestones).selectinload(RoadmapMilestone.skills))
    )
    roadmap = result.scalar_one_or_none()
    if roadmap is None:
        raise NotFoundError("Roadmap not found.")
    return roadmap


async def _get_owned_skill(
    db: AsyncSession, user: User, roadmap_id: uuid.UUID, skill_id: uuid.UUID
) -> tuple[Roadmap, RoadmapSkill]:
    """Fetch a `RoadmapSkill` that genuinely belongs to a roadmap this user owns — never trusts `skill_id` alone."""
    roadmap = await _get_owned_roadmap(db, user, roadmap_id)
    for milestone in roadmap.milestones:
        for skill in milestone.skills:
            if skill.id == skill_id:
                return roadmap, skill
    raise NotFoundError("Roadmap skill not found.")


def _milestones_to_orm(milestones: list[dict]) -> list[RoadmapMilestone]:
    """Convert the pipeline's plain-dict milestone/skill drafts into persistable ORM rows, in pipeline order (`order_index` set explicitly rather than relying on insertion order)."""
    orm_milestones: list[RoadmapMilestone] = []
    for m_index, milestone in enumerate(milestones):
        orm_skills = [
            RoadmapSkill(
                skill_name=skill["skill_name"],
                importance=skill.get("importance"),
                estimated_hours=skill.get("estimated_hours"),
                status=skill.get("status", "not_started"),
                resources=skill.get("resources", []),
                study_material=skill.get("study_material", {}),
                practice_activities=skill.get("practice_activities", {}),
                lateral_connections=skill.get("lateral_connections", []),
                order_index=s_index,
            )
            for s_index, skill in enumerate(milestone.get("skills", []))
        ]
        orm_milestones.append(
            RoadmapMilestone(
                title=milestone["title"],
                timeframe_label=milestone.get("timeframe_label"),
                skills=orm_skills,
                order_index=m_index,
            )
        )
    return orm_milestones


async def _roadmap_read_response(
    db: AsyncSession, user: User, roadmap_id: uuid.UUID, final_state: dict
) -> RoadmapRead:
    """Eager-load milestones/skills before Pydantic validation (async SQLAlchemy safe)."""
    roadmap = await _get_owned_roadmap(db, user, roadmap_id)
    roadmap_read = RoadmapRead.model_validate(roadmap)
    roadmap_read.generation_confidence = final_state.get("confidence_score", 0.0)
    roadmap_read.generation_citations = final_state.get("citations", [])
    return roadmap_read


async def _existing_profile_skill_names(db: AsyncSession, user: User) -> list[str]:
    """The user's own Profile.skills names — lets `SkillDecomposerAgent` mark roadmap skills the user already has as `already_known` instead of scheduling redundant study time for them."""
    profile = await _get_or_create_profile(db, user)
    return [s.name for s in profile.skills]


@router.post("/generate", response_model=RoadmapRead, status_code=201)
async def generate_roadmap(
    payload: RoadmapGenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RoadmapRead:
    """Run the full 9-node Career Roadmap generation pipeline and persist the result as a new `Roadmap` row."""
    existing_skills = await _existing_profile_skill_names(db, user)
    personalization_inputs = payload.personalization_inputs.model_dump()

    result = await run_roadmap_generation_pipeline(
        user_id=str(user.id),
        target_role=payload.target_role,
        pace=payload.pace,
        starting_skill_level=payload.starting_skill_level,
        personalization_inputs=personalization_inputs,
        existing_profile_skills=existing_skills,
    )
    final_state = result["state"]
    cost_monitor = result["cost_monitor"]
    draft = final_state.get("draft_output") or {}

    roadmap = Roadmap(
        user_id=user.id,
        target_role=payload.target_role,
        pace=payload.pace,
        starting_skill_level=payload.starting_skill_level,
        personalization_inputs=personalization_inputs,
        milestones=_milestones_to_orm(draft.get("milestones", [])),
    )
    db.add(roadmap)
    await db.commit()
    roadmap_id = roadmap.id

    await cost_monitor.persist(db, user_id=str(user.id), model_used=final_state.get("model_tier_used", "unknown"))
    await db.commit()  # CostMonitor.persist() only flushes — commit explicitly so the usage record survives session close

    return await _roadmap_read_response(db, user, roadmap_id, final_state)


@router.get("/", response_model=list[RoadmapRead])
async def list_roadmaps(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Roadmap]:
    """All roadmaps the current user has generated, most recently created first."""
    result = await db.execute(
        select(Roadmap)
        .where(Roadmap.user_id == user.id)
        .options(selectinload(Roadmap.milestones).selectinload(RoadmapMilestone.skills))
        .order_by(Roadmap.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{roadmap_id}", response_model=RoadmapRead)
async def get_roadmap(
    roadmap_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Roadmap:
    return await _get_owned_roadmap(db, user, roadmap_id)


@router.delete("/{roadmap_id}", status_code=204)
async def delete_roadmap(
    roadmap_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    roadmap = await _get_owned_roadmap(db, user, roadmap_id)
    await db.delete(roadmap)
    await db.commit()
    return Response(status_code=204)


@router.post("/{roadmap_id}/regenerate", response_model=RoadmapRead)
async def regenerate_roadmap(
    roadmap_id: uuid.UUID,
    payload: RoadmapGenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RoadmapRead:
    """Re-run roadmap generation (e.g. after changing pace or personalization inputs) against an existing roadmap row, replacing its milestones/skills in place rather than creating a new row."""
    roadmap = await _get_owned_roadmap(db, user, roadmap_id)
    existing_skills = await _existing_profile_skill_names(db, user)
    personalization_inputs = payload.personalization_inputs.model_dump()

    result = await run_roadmap_generation_pipeline(
        user_id=str(user.id),
        target_role=payload.target_role,
        pace=payload.pace,
        starting_skill_level=payload.starting_skill_level,
        personalization_inputs=personalization_inputs,
        existing_profile_skills=existing_skills,
    )
    final_state = result["state"]
    cost_monitor = result["cost_monitor"]
    draft = final_state.get("draft_output") or {}

    roadmap.target_role = payload.target_role
    roadmap.pace = payload.pace
    roadmap.starting_skill_level = payload.starting_skill_level
    roadmap.personalization_inputs = personalization_inputs
    roadmap.milestones = _milestones_to_orm(draft.get("milestones", []))  # cascade="all, delete-orphan" cleans up the old rows
    await db.commit()

    await cost_monitor.persist(db, user_id=str(user.id), model_used=final_state.get("model_tier_used", "unknown"))
    await db.commit()  # CostMonitor.persist() only flushes — commit explicitly so the usage record survives session close

    return await _roadmap_read_response(db, user, roadmap.id, final_state)


@router.patch("/{roadmap_id}/skills/{skill_id}/status", response_model=RoadmapSkillRead)
async def update_skill_status(
    roadmap_id: uuid.UUID,
    skill_id: uuid.UUID,
    payload: RoadmapSkillStatusUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RoadmapSkill:
    """Mark a roadmap skill not_started/in_progress/completed — pure data update, no agent pipeline involved."""
    _, skill = await _get_owned_skill(db, user, roadmap_id, skill_id)
    skill.status = payload.status
    await db.commit()
    await db.refresh(skill)
    return skill


@router.post("/{roadmap_id}/skills/{skill_id}/refresh", response_model=RoadmapSkillRead)
async def refresh_skill_content(
    roadmap_id: uuid.UUID,
    skill_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RoadmapSkill:
    """Regenerate just this skill's resources/study material/practice activities (e.g. for fresher material) without re-running full roadmap generation."""
    roadmap, skill = await _get_owned_skill(db, user, roadmap_id, skill_id)

    result = await run_skill_refresh_pipeline(
        user_id=str(user.id),
        skill_name=skill.skill_name,
        target_role=roadmap.target_role,
        skill_importance=skill.importance,
    )
    final_state = result["state"]
    cost_monitor = result["cost_monitor"]
    draft = final_state.get("draft_output") or {}

    skill.resources = draft.get("resources", skill.resources)
    skill.study_material = draft.get("study_material", skill.study_material)
    skill.practice_activities = draft.get("practice_activities", skill.practice_activities)
    skill.lateral_connections = draft.get("lateral_connections", skill.lateral_connections)
    await db.commit()
    await db.refresh(skill)

    await cost_monitor.persist(db, user_id=str(user.id), model_used=final_state.get("model_tier_used", "unknown"))
    await db.commit()  # CostMonitor.persist() only flushes — commit explicitly so the usage record survives session close

    return skill
