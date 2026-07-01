"""
agents/common/graph_utils.py
================================
LangGraph `StateGraph` wiring shared by every feature pipeline. Every
feature builds the SAME shape of graph — Guardrail -> Planner -> Executor ->
Reflector, with a conditional edge looping Reflector back to Executor for
up to `max_revisions` rounds — so that wiring is written once here instead
of being copy-pasted across four feature packages.

    START -> guardrail --(rejected)--> END
                |(passed)
                v
             planner -> executor -> reflector --(should_revise)--> executor
                                        |(done)
                                        v
                                       END

Features that need extra nodes (e.g. Job Search's CrossVerifierAgent
running between Executor and Reflector) build their own graph using the
same node/router building blocks exposed here rather than forcing every
feature through one rigid shape — see `build_revision_pipeline()`'s
`extra_nodes` parameter and each feature's own `graph.py` for examples.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from app.agents.common.base import BaseAgent
from app.core.logging import get_logger

logger = get_logger(__name__)


def guardrail_router(state: dict[str, Any]) -> str:
    """Conditional edge after Guardrail: stop immediately on rejection rather than wasting a Planner/Executor call."""
    return "rejected" if not state.get("guardrail_passed", True) else "passed"


def reflector_router(state: dict[str, Any]) -> str:
    """Conditional edge after Reflector: loop back to the Executor while `_should_revise` is set, otherwise finish."""
    return "revise" if state.get("_should_revise") else "done"


def build_revision_pipeline(
    *,
    guardrail: BaseAgent,
    planner: BaseAgent,
    executor: BaseAgent,
    reflector: BaseAgent,
    state_schema: type,
    extra_nodes: dict[str, BaseAgent] | None = None,
    executor_to_reflector_via: str | None = None,
) -> Any:
    """
    Assemble and compile the standard Guardrail -> Planner -> Executor ->
    Reflector graph (with Executor<->Reflector revision looping) shared by
    every feature pipeline.

    Args:
        guardrail/planner/executor/reflector: the four required agents.
        state_schema: the feature's `TypedDict` (extending `BaseAgentState`)
            describing this pipeline's full state shape.
        extra_nodes: additional `{name: agent}` nodes to register on the
            graph. Registering a node here does NOT automatically wire it
            into the edge sequence — pass `executor_to_reflector_via` to
            insert exactly one extra node between Executor and Reflector
            (the common case, e.g. CrossVerifierAgent), or build a fully
            custom edge sequence in the feature's own graph.py for
            anything more elaborate.
        executor_to_reflector_via: if set, must be a key present in
            `extra_nodes` — routes Executor -> that node -> Reflector
            instead of Executor -> Reflector directly.
    """
    graph = StateGraph(state_schema)

    graph.add_node("guardrail", guardrail.as_node())
    graph.add_node("planner", planner.as_node())
    graph.add_node("executor", executor.as_node())
    graph.add_node("reflector", reflector.as_node())

    for node_name, agent in (extra_nodes or {}).items():
        graph.add_node(node_name, agent.as_node())

    graph.set_entry_point("guardrail")
    graph.add_conditional_edges("guardrail", guardrail_router, {"rejected": END, "passed": "planner"})
    graph.add_edge("planner", "executor")

    if executor_to_reflector_via:
        graph.add_edge("executor", executor_to_reflector_via)
        graph.add_edge(executor_to_reflector_via, "reflector")
    else:
        graph.add_edge("executor", "reflector")

    graph.add_conditional_edges("reflector", reflector_router, {"revise": "executor", "done": END})

    compiled = graph.compile()
    logger.info("agent_graph_compiled", extra_nodes=list((extra_nodes or {}).keys()))
    return compiled


def initial_state(*, feature: str, user_id: str, request_id: str, **extra: Any) -> dict[str, Any]:
    """
    Build the common opening state dict every feature's `run_*_pipeline()`
    entry point starts from, with `revision_count` pre-seeded to 0 so the
    Reflector's `revision_count < max_revisions` check works on the very
    first pass without every caller remembering to set it.
    """
    return {
        "feature": feature,
        "user_id": user_id,
        "request_id": request_id,
        "revision_count": 0,
        "citations": [],
        **extra,
    }
