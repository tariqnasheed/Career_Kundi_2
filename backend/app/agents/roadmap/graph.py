"""
agents/roadmap/graph.py
=============================
Pipeline entry points for the Career Roadmap feature (§4.5). Route handlers
in `app/api/routes/roadmap.py` call ONLY `run_roadmap_generation_pipeline()`
and `run_skill_refresh_pipeline()` — every LangGraph/agent detail lives here.

The full roadmap-generation pipeline has MORE distinct stages than the
shared Guardrail -> Planner -> Executor -> Reflector shape (RoleTaxonomy,
SkillDecomposer, ResourceFinder, StudyMaterial, PracticeGenerator, and
TimelineOptimizer all sit between Planner and Reflector — six stages where
`build_revision_pipeline()`'s `executor_to_reflector_via` only supports
ONE), so this module hand-builds its own `StateGraph` using the same
node/router building blocks (`BaseAgent.as_node()`, `guardrail_router`,
`reflector_router`) rather than forcing the feature through a shape it
doesn't fit, per `graph_utils.py`'s own documented escape hatch.

The lightweight single-skill refresh pipeline DOES fit the standard shape,
so it's built with `build_revision_pipeline()` directly — see
`run_skill_refresh_pipeline()` below.

    START -> guardrail --(rejected)--> END
                |(passed)
                v
             planner -> role_taxonomy -> skill_decomposer -> resource_finder
                            -> study_material -> practice_generator -> timeline_optimizer
                            -> reflector --(revise)--> skill_decomposer
                                  |(done)
                                  v
                                 END

On revision, the loop re-enters at `skill_decomposer` rather than
`role_taxonomy` — the resolved role/skill taxonomy is a stable lookup or
heuristic that the Reflector's domain checks never flag, so re-running it
on every revision round would be wasted work (and, for novel roles, a
redundant `ensure_role_node` graph mutation).
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from langgraph.graph import END, StateGraph

from app.agents.common.cost_monitor import CostMonitor
from app.agents.common.graph_utils import build_revision_pipeline, guardrail_router, initial_state, reflector_router
from app.agents.common.guardrail import raise_if_guardrail_failed
from app.core.logging import get_logger

from .agents import (
    PracticeGeneratorAgent,
    ResourceFinderAgent,
    RoadmapGuardrailAgent,
    RoadmapPlannerAgent,
    RoadmapReflectorAgent,
    RoleTaxonomyAgent,
    SkillDecomposerAgent,
    SkillRefreshExecutorAgent,
    SkillRefreshGuardrailAgent,
    SkillRefreshPlannerAgent,
    SkillRefreshReflectorAgent,
    StudyMaterialAgent,
    TimelineOptimizerAgent,
)
from .state import RoadmapGenerationState, SkillContentRefreshState

logger = get_logger(__name__)


def _build_roadmap_generation_graph(cost_monitor: CostMonitor) -> Any:
    graph = StateGraph(RoadmapGenerationState)

    guardrail = RoadmapGuardrailAgent()
    planner = RoadmapPlannerAgent(cost_monitor)
    role_taxonomy = RoleTaxonomyAgent(cost_monitor)
    skill_decomposer = SkillDecomposerAgent()
    resource_finder = ResourceFinderAgent()
    study_material = StudyMaterialAgent(cost_monitor)
    practice_generator = PracticeGeneratorAgent(cost_monitor)
    timeline_optimizer = TimelineOptimizerAgent()
    reflector = RoadmapReflectorAgent()

    graph.add_node("guardrail", guardrail.as_node())
    graph.add_node("planner", planner.as_node())
    graph.add_node("role_taxonomy", role_taxonomy.as_node())
    graph.add_node("skill_decomposer", skill_decomposer.as_node())
    graph.add_node("resource_finder", resource_finder.as_node())
    graph.add_node("study_material", study_material.as_node())
    graph.add_node("practice_generator", practice_generator.as_node())
    graph.add_node("timeline_optimizer", timeline_optimizer.as_node())
    graph.add_node("reflector", reflector.as_node())

    graph.set_entry_point("guardrail")
    graph.add_conditional_edges("guardrail", guardrail_router, {"rejected": END, "passed": "planner"})
    graph.add_edge("planner", "role_taxonomy")
    graph.add_edge("role_taxonomy", "skill_decomposer")
    graph.add_edge("skill_decomposer", "resource_finder")
    graph.add_edge("resource_finder", "study_material")
    graph.add_edge("study_material", "practice_generator")
    graph.add_edge("practice_generator", "timeline_optimizer")
    graph.add_edge("timeline_optimizer", "reflector")
    graph.add_conditional_edges("reflector", reflector_router, {"revise": "skill_decomposer", "done": END})

    compiled = graph.compile()
    logger.info("agent_graph_compiled", feature="roadmap", nodes=9)
    return compiled


async def run_roadmap_generation_pipeline(
    *,
    user_id: str,
    target_role: str,
    pace: str = "normal",
    starting_skill_level: str | None = None,
    personalization_inputs: dict[str, Any] | None = None,
    existing_profile_skills: list[str] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Run the full 9-node Career Roadmap generation pipeline for a target role."""
    cost_monitor = CostMonitor(feature="roadmap")
    graph = _build_roadmap_generation_graph(cost_monitor)

    personalization_inputs = personalization_inputs or {}
    raw_input_text = json.dumps(
        {"target_role": target_role, "pace": pace, "personalization_inputs": personalization_inputs}
    )

    state = initial_state(
        feature="roadmap",
        user_id=user_id,
        request_id=request_id or uuid.uuid4().hex,
        raw_input=raw_input_text,
        target_role=target_role,
        pace=pace,
        starting_skill_level=starting_skill_level,
        personalization_inputs=personalization_inputs,
        existing_profile_skills=existing_profile_skills or [],
    )
    final_state = await graph.ainvoke(state)
    raise_if_guardrail_failed(final_state)

    logger.info(
        "roadmap_generation_pipeline_completed",
        confidence=final_state.get("confidence_score"),
        revisions=final_state.get("revision_count"),
        **cost_monitor.summary(),
    )
    return {"state": final_state, "cost_monitor": cost_monitor}


async def run_skill_refresh_pipeline(
    *,
    user_id: str,
    skill_name: str,
    target_role: str,
    skill_importance: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Run the lightweight single-skill content refresh pipeline — regenerate one skill's resources/study material/practice activities without re-running full roadmap generation."""
    cost_monitor = CostMonitor(feature="roadmap_skill_refresh")
    graph = build_revision_pipeline(
        guardrail=SkillRefreshGuardrailAgent(),
        planner=SkillRefreshPlannerAgent(cost_monitor),
        executor=SkillRefreshExecutorAgent(cost_monitor),
        reflector=SkillRefreshReflectorAgent(),
        state_schema=SkillContentRefreshState,
    )

    raw_input_text = f"Refresh content for skill '{skill_name}' (target role: {target_role})."
    state = initial_state(
        feature="roadmap_skill_refresh",
        user_id=user_id,
        request_id=request_id or uuid.uuid4().hex,
        raw_input=raw_input_text,
        skill_name=skill_name,
        target_role=target_role,
        skill_importance=skill_importance,
    )
    final_state = await graph.ainvoke(state)
    raise_if_guardrail_failed(final_state)

    logger.info(
        "skill_refresh_pipeline_completed",
        confidence=final_state.get("confidence_score"),
        **cost_monitor.summary(),
    )
    return {"state": final_state, "cost_monitor": cost_monitor}
