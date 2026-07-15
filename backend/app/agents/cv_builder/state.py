"""
agents/cv_builder/state.py
===============================
State shapes for the two LangGraph pipelines in this feature package (§4.3
CV Builder):

- `CVGenerationState` — Guardrail -> Planner -> Executor -> Reflector. Input
  is a full profile snapshot (+ optional target job snapshot); output is a
  `CVGenerationResult` (see app/schemas/cv_builder.py) that `render.py`
  turns into `GeneratedCV.rendered_content` AFTER the graph succeeds.
- `BulletImprovementState` — the same four stages, scoped to a single
  bullet (the "Improve with AI" button next to one Profile entry).

Both extend `BaseAgentState`. Note the deliberate absence of ANY scraping or
template-rendering state here — per the platform-wide design principle
("scraping happens before the graph" in job_search/graph.py), deterministic,
non-generative steps live OUTSIDE the graph: loading the Profile happens in
the route layer before `run_cv_generation_pipeline()` is called, and
rendering the approved draft into `GeneratedCV.rendered_content` happens in
`render.py` after it returns.
"""

from __future__ import annotations

from typing import Any

from app.agents.common.state import BaseAgentState


class CVGenerationState(BaseAgentState, total=False):
    # --- Input ---
    raw_input: str  # serialized free-text profile content the Guardrail vets (headline, bio, all bullets)
    profile_snapshot: dict[str, Any]  # full nested Profile, as a plain dict (ProfileRead.model_dump())
    target_job_snapshot: dict[str, Any] | None  # a SavedJob's fields, if tailoring toward a specific role
    requested_section_ids: list[str] | None  # None = every section the profile has data for
    tone: str  # concise | detailed | executive
    generation_mode: str  # profile | role_targeted | quick_intake
    target_role_title: str | None
    target_role_description: str | None
    career_level: str | None  # beginner | intermediate | advanced | expert (quick_intake)


class BulletImprovementState(BaseAgentState, total=False):
    # --- Input ---
    raw_input: str  # the bullet text itself, vetted by the Guardrail
    bullet_text: str
    bullet_context: dict[str, Any]  # {"role_title": ..., "company_name": ..., "section_type": ...}
    target_job_snapshot: dict[str, Any] | None
