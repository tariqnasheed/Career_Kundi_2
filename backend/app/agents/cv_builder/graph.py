"""
agents/cv_builder/graph.py
===============================
Pipeline entry points for the CV Builder feature (§4.3). Route handlers in
`app/api/routes/cv_builder.py` call ONLY `run_cv_generation_pipeline()` and
`run_bullet_improvement_pipeline()` — every LangGraph/agent detail
(Guardrail -> Planner -> Executor -> Reflector, RAG retrieval, the
fabrication safety net) is encapsulated here, mirroring
`app/agents/job_search/graph.py`.

Design note — rendering happens AFTER the graph runs
-----------------------------------------------------
Same principle as job_search's "scraping happens before the graph": turning
an APPROVED `CVGenerationResult` into the section-by-section
`GeneratedCV.rendered_content` JSON (`render.py::render_cv`) is deterministic
template assembly, not a quality-gated generation step, so it is NOT a graph
node. The route layer calls `render_cv()` itself, after this module returns
the Reflector-approved draft.
"""

from __future__ import annotations

import uuid
from typing import Any

from app.agents.common.cost_monitor import CostMonitor
from app.agents.common.graph_utils import build_revision_pipeline, initial_state
from app.agents.common.guardrail import raise_if_guardrail_failed
from app.core.logging import get_logger

from .agents import (
    BulletImprovementExecutorAgent,
    BulletImprovementGuardrailAgent,
    BulletImprovementPlannerAgent,
    BulletImprovementReflectorAgent,
    CVBuilderGuardrailAgent,
    CVBulletWriterExecutorAgent,
    CVPlannerAgent,
    CVReflectorAgent,
)
from .mock_data import profile_text_blob
from .state import BulletImprovementState, CVGenerationState

logger = get_logger(__name__)


async def run_cv_generation_pipeline(
    *,
    user_id: str,
    profile_snapshot: dict[str, Any],
    target_job_snapshot: dict[str, Any] | None = None,
    requested_section_ids: list[str] | None = None,
    tone: str = "concise",
    generation_mode: str = "profile",
    target_role_title: str | None = None,
    target_role_description: str | None = None,
    career_level: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Run the full CV generation pipeline against a profile snapshot (the
    output of `ProfileRead.model_validate(profile).model_dump(mode="json")`
    plus the route-injected `full_name`/`email`, see api/routes/cv_builder.py)
    and an optional target-job snapshot to tailor toward.

    `generation_mode=quick_intake` uses a deterministic honest starter draft
    (no invented employers/degrees/certs); the snapshot is built by the route
    from manual intake fields without mutating Profile/Passport.
    """
    cost_monitor = CostMonitor(feature="cv_builder")
    graph = build_revision_pipeline(
        guardrail=CVBuilderGuardrailAgent(),
        planner=CVPlannerAgent(cost_monitor),
        executor=CVBulletWriterExecutorAgent(cost_monitor),
        reflector=CVReflectorAgent(),
        state_schema=CVGenerationState,
    )

    raw_input_text = profile_text_blob(profile_snapshot) or "(empty profile)"
    state = initial_state(
        feature="cv_builder",
        user_id=user_id,
        request_id=request_id or uuid.uuid4().hex,
        raw_input=raw_input_text,
        profile_snapshot=profile_snapshot,
        target_job_snapshot=target_job_snapshot,
        requested_section_ids=requested_section_ids,
        tone=tone,
        generation_mode=generation_mode,
        target_role_title=target_role_title,
        target_role_description=target_role_description,
        career_level=career_level,
    )
    final_state = await graph.ainvoke(state)
    raise_if_guardrail_failed(final_state)

    logger.info(
        "cv_generation_pipeline_completed",
        confidence=final_state.get("confidence_score"),
        revisions=final_state.get("revision_count"),
        **cost_monitor.summary(),
    )
    return {"state": final_state, "cost_monitor": cost_monitor}


async def run_bullet_improvement_pipeline(
    *,
    user_id: str,
    bullet_text: str,
    bullet_context: dict[str, Any],
    target_job_snapshot: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Run the lightweight single-bullet improvement pipeline used by the Profile page's 'Improve with AI' button."""
    cost_monitor = CostMonitor(feature="cv_bullet_improvement")
    graph = build_revision_pipeline(
        guardrail=BulletImprovementGuardrailAgent(),
        planner=BulletImprovementPlannerAgent(cost_monitor),
        executor=BulletImprovementExecutorAgent(cost_monitor),
        reflector=BulletImprovementReflectorAgent(),
        state_schema=BulletImprovementState,
    )

    state = initial_state(
        feature="cv_bullet_improvement",
        user_id=user_id,
        request_id=request_id or uuid.uuid4().hex,
        raw_input=bullet_text,
        bullet_text=bullet_text,
        bullet_context=bullet_context,
        target_job_snapshot=target_job_snapshot,
    )
    final_state = await graph.ainvoke(state)
    raise_if_guardrail_failed(final_state)

    logger.info(
        "bullet_improvement_pipeline_completed",
        confidence=final_state.get("confidence_score"),
        **cost_monitor.summary(),
    )
    return {"state": final_state, "cost_monitor": cost_monitor}
