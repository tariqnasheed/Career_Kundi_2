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


class RoadmapTaxonomyMeta(BaseModel):
    """
    Optional advisory Role Intelligence payload nested under
    personalization_inputs._taxonomy (0051-F10). Never required for generate.
    Decoupled from agents.roadmap.RoleTaxonomyAgent.
    """

    target_role_text: str | None = None
    matched_role_id: str | None = None
    matched_skill_id: str | None = None
    normalized_text: str | None = None
    source: str | None = None
    confidence: str | None = None
    explanation: str | None = None
    accepted_by_user: bool = False
    kept_freeform: bool = False
    suggested_skill_ids: list[str] = Field(default_factory=list)
    suggested_skill_labels: list[str] = Field(default_factory=list)
    matched_role_title: str | None = None


class RoadmapPersonalizationInputs(BaseModel):
    """
    Optional steering inputs beyond `target_role`/`pace`/`starting_skill_level`.
    Every field is optional — the TimelineOptimizerAgent falls back to
    pace-derived defaults (see `app/agents/roadmap/mock_data.py`) when these
    are left unset.

    `_taxonomy` is optional advisory metadata (0051-F10) and must not affect
    generation when absent or unknown.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    weekly_hours_available: float | None = Field(
        default=None, gt=0, description="Overrides the pace-derived default weekly study-hours budget."
    )
    preferred_learning_style: Literal["visual", "reading", "hands_on", "mixed"] | None = None
    target_timeframe_months: int | None = Field(default=None, gt=0)
    additional_context: str | None = Field(
        default=None, description="Free-text context, e.g. 'I already know basic SQL from a bootcamp.'"
    )
    taxonomy: RoadmapTaxonomyMeta | None = Field(
        default=None,
        alias="_taxonomy",
        description="Optional advisory Role Intelligence meta nested as personalization_inputs._taxonomy",
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
    curated: bool = False


class RoadmapKeyConcept(BaseModel):
    """A single teachable concept: the term plus a plain-language definition."""

    term: str = ""
    definition: str = ""


class RoadmapStudyMaterial(BaseModel):
    # --- Core (backward compatible) ---
    overview: str = ""
    key_concepts: list[str] = Field(default_factory=list)
    estimated_reading_time_minutes: int | None = None
    # --- Enriched, Bloom-aligned learning content ---
    why_it_matters: str = ""
    prerequisites: list[str] = Field(default_factory=list)
    learning_objectives: list[str] = Field(default_factory=list)
    beginner_explanation: str = ""
    intermediate_explanation: str = ""
    advanced_explanation: str = ""
    concepts: list[RoadmapKeyConcept] = Field(default_factory=list)
    worked_example: str = ""
    common_mistakes: list[str] = Field(default_factory=list)
    revision_notes: list[str] = Field(default_factory=list)


class RoadmapFlashcard(BaseModel):
    """Active-recall flashcard (spaced-repetition ready): prompt -> answer."""

    front: str = ""
    back: str = ""


class RoadmapQuizQuestion(BaseModel):
    """A multiple-choice 'assessment gateway' checkpoint question."""

    question: str = ""
    options: list[str] = Field(default_factory=list)
    answer_index: int = 0
    explanation: str = ""


class RoadmapProject(BaseModel):
    """A hands-on, project-based-learning brief at a stated difficulty."""

    title: str = ""
    brief: str = ""
    steps: list[str] = Field(default_factory=list)
    deliverable: str = ""
    difficulty: Literal["beginner", "intermediate", "advanced"] = "beginner"


class RoadmapPracticeActivities(BaseModel):
    # --- Core (backward compatible) ---
    exercises: list[str] = Field(default_factory=list)
    project_idea: str | None = None
    self_assessment_questions: list[str] = Field(default_factory=list)
    # --- Enriched practice modalities ---
    flashcards: list[RoadmapFlashcard] = Field(default_factory=list)
    quizzes: list[RoadmapQuizQuestion] = Field(default_factory=list)
    projects: list[RoadmapProject] = Field(default_factory=list)
    reflection_questions: list[str] = Field(default_factory=list)


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
