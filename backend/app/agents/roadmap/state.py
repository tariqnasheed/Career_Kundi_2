"""
agents/roadmap/state.py
============================
State shapes for the two LangGraph pipelines in this feature package (§4.5
Career Roadmap):

- `RoadmapGenerationState` — the full 6-stage pipeline:
  Guardrail -> Planner -> RoleTaxonomy -> SkillDecomposer -> ResourceFinder
  -> StudyMaterial -> PracticeGenerator -> TimelineOptimizer -> Reflector.
  Input is a target role + pace + starting skill level + personalization
  inputs; output is a full milestone/skill tree ready to persist as a
  `Roadmap` row (see app/db/models/roadmap.py).
- `SkillContentRefreshState` — the lightweight single-skill pipeline used
  when a user wants to regenerate just one skill's resources/study
  material/practice activities (e.g. after marking it "in_progress" and
  wanting fresher material), built on the standard
  `build_revision_pipeline()` shape rather than the hand-built graph above.

Both extend `BaseAgentState` so the shared Guardrail/Reflector/graph_utils
code operates on them without modification.
"""

from __future__ import annotations

from typing import Any

from app.agents.common.state import BaseAgentState


class RoadmapGenerationState(BaseAgentState, total=False):
    # --- Input ---
    raw_input: str  # serialized request blob the Guardrail vets (target role + pace + free-text context)
    target_role: str
    pace: str  # "fast" | "normal" | "thorough"
    starting_skill_level: str | None
    personalization_inputs: dict[str, Any]
    existing_profile_skills: list[str]  # skill names already on the user's Profile, used to mark skills "already known"

    # --- RoleTaxonomy stage ---
    role_taxonomy: dict[str, Any]  # {"canonical_role", "is_novel_role", "industries", "required_skills"}

    # --- SkillDecomposer / ResourceFinder / StudyMaterial / PracticeGenerator stage ---
    roadmap_skills: list[dict[str, Any]]  # flat, dependency-ordered list; grouped into milestones by TimelineOptimizer

    # --- TimelineOptimizer stage ---
    milestones: list[dict[str, Any]]


class SkillContentRefreshState(BaseAgentState, total=False):
    # --- Input ---
    raw_input: str  # serialized skill_name + target_role context the Guardrail vets
    skill_name: str
    target_role: str
    skill_importance: str | None
