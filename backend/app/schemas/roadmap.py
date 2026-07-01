"""
schemas/roadmap.py
=======================
Pydantic request/response contracts for the Career Roadmap feature (§4.5).

Per the platform-wide "no artificial limits" mandate, list fields
(`milestones`, `skills`, `resources`, `key_concepts`, `exercises`, ...) carry
no `max_length`/`max_items` constraint — the agent pipeline, not the schema
layer, decides how many items are genuinely warranted by the target role and
the user's personalization inputs.

Field names on the `*Read` models are kept in exact lockstep with
`app/db/models/roadmap.py` (`Roadmap` / `RoadmapMilestone` / `RoadmapSkill`)
so `model_validate(orm_row)` round-trips cleanly.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class _ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Request -------------------------------------------------------------------------


class RoadmapPersonalizationInputs(BaseModel):
    """
    Optional steering inputs beyond `target_role`/`pace`/`starting_skill_level`.
    Every field is optional — the TimelineOptimizerAgent falls back to
    pace-derived defaults (see `app/agents/roadmap/mock_data.py`) when these
    are left unset.
    """

    weekly_hours_available: float | None = Field(
        default=None, gt=0, description="Overrides the pace-derived default weekly study-hours budget."
    )
    preferred_learning_style: Literal["visual", "reading", "hands_on", "mixed"] | None = None
    target_timeframe_months: int | None = Field(default=None, gt=0)
    additional_context: str | None = Field(
        default=None, description="Free-text context, e.g. 'I already know basic SQL from a bootcamp.'"
    )


class RoadmapGenerateRequest(BaseModel):
    target_role: str = Field(min_length=2, max_length=255)
    pace: Literal["fast", "normal", "thorough"] = "normal"
    starting_skill_level: Literal["beginner", "intermediate", "advanced"] | None = None
    personalization_inputs: RoadmapPersonalizationInputs = Field(default_factory=RoadmapPersonalizationInputs)


class RoadmapSkillStatusUpdate(BaseModel):
    status: Literal["not_started", "in_progress", "completed"]


# --- Per-skill generated content blobs ------------------------------------------------


class RoadmapResourceItem(BaseModel):
    title: str
    url: str | None = None
    resource_type: Literal["course", "documentation", "article", "book", "video", "search_result"] = "article"
    source: str | None = None
    verified: bool = False


class RoadmapStudyMaterial(BaseModel):
    overview: str = ""
    key_concepts: list[str] = Field(default_factory=list)
    estimated_reading_time_minutes: int | None = None


class RoadmapPracticeActivities(BaseModel):
    exercises: list[str] = Field(default_factory=list)
    project_idea: str | None = None
    self_assessment_questions: list[str] = Field(default_factory=list)


# --- Response --------------------------------------------------------------------------


class RoadmapSkillRead(_ORMModel):
    id: uuid.UUID
    skill_name: str
    importance: str | None = None
    estimated_hours: float | None = None
    status: Literal["not_started", "in_progress", "completed"] = "not_started"
    resources: list[RoadmapResourceItem] = Field(default_factory=list)
    study_material: RoadmapStudyMaterial = Field(default_factory=RoadmapStudyMaterial)
    practice_activities: RoadmapPracticeActivities = Field(default_factory=RoadmapPracticeActivities)
    lateral_connections: list[str] = Field(default_factory=list)


class RoadmapMilestoneRead(_ORMModel):
    id: uuid.UUID
    title: str
    timeframe_label: str | None = None
    skills: list[RoadmapSkillRead] = Field(default_factory=list)


class RoadmapRead(_ORMModel):
    id: uuid.UUID
    target_role: str
    pace: Literal["fast", "normal", "thorough"]
    starting_skill_level: str | None = None
    personalization_inputs: dict = Field(default_factory=dict)
    milestones: list[RoadmapMilestoneRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    # Not persisted on the `Roadmap` row itself (it has no confidence/citations
    # column — see db/models/roadmap.py) — populated by the route layer
    # straight off the pipeline's final state at generation time, and simply
    # absent (default) on every subsequent GET/list call.
    generation_confidence: float | None = None
    generation_citations: list[dict] = Field(default_factory=list)


class RoleTaxonomyInfo(BaseModel):
    """Surfaced alongside a freshly-generated roadmap so the UI can show 'why these skills'."""

    canonical_role: str
    is_novel_role: bool = False
    industries: list[str] = Field(default_factory=list)
    requires_manual_skill_input: bool = False
