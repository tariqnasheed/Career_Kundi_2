"""
agents/chatbot/graph.py
===========================
Pipeline entry point for the AI Assistant Chatbot (§4.7).

Route handlers in `app/api/routes/chatbot.py` call ONLY
`run_chat_turn_pipeline()` — every LangGraph / agent detail lives here.

The chatbot pipeline needs MORE stages than the standard
Guardrail → Planner → Executor → Reflector shape because MemoryAgent,
IntentClassifierAgent, and ActionDispatchAgent all sit between the
Guardrail and the Planner, and `build_revision_pipeline()`'s
`executor_to_reflector_via` only supports ONE extra node.  This module
therefore hand-builds its own `StateGraph` following the same established
escape-hatch documented in `graph_utils.py` and used by the Roadmap
feature's 9-node graph.

Pipeline topology:

    START → guardrail ──(rejected)──► END
                │(passed)
                ▼
          memory_agent
                │
                ▼
       intent_classifier
                │
                ▼
       action_dispatch
                │
                ▼
            planner
                │
                ▼
           executor ◄────────────────────┐
                │                        │
                ▼                        │
           reflector ──(revise)──────────┘
                │(done)
                ▼
               END

On revision, the loop re-enters at `executor` only — MemoryAgent,
IntentClassifierAgent, ActionDispatchAgent, and ChatbotPlannerAgent are
all stable per-turn decisions (the retrieved context, intent, and tier
don't change because the Reflector found an issue in the prose), so
re-running them on every revision round would be both wasteful and likely
to produce a different intent classification for the same message.
"""

from __future__ import annotations

import uuid
from typing import Any

from langgraph.graph import END, StateGraph

from app.agents.common.cost_monitor import CostMonitor
from app.agents.common.graph_utils import guardrail_router, initial_state, reflector_router
from app.agents.common.guardrail import raise_if_guardrail_failed
from app.core.logging import get_logger

from .agents import (
    ActionDispatchAgent,
    ChatbotGuardrailAgent,
    ChatbotPlannerAgent,
    ChatbotReflectorAgent,
    ChatbotResponseExecutorAgent,
    IntentClassifierAgent,
    MemoryAgent,
)
from .state import ChatbotConversationState

logger = get_logger(__name__)


def _build_chatbot_graph(cost_monitor: CostMonitor) -> Any:
    """
    Compile the 7-node chatbot StateGraph once per pipeline invocation
    (each HTTP request creates a fresh CostMonitor, so the graph is not
    cached — it's fast to build and keeps the cost monitor properly scoped
    to the single in-flight request).
    """
    graph = StateGraph(ChatbotConversationState)

    guardrail = ChatbotGuardrailAgent()
    memory_agent = MemoryAgent()
    intent_classifier = IntentClassifierAgent(cost_monitor)
    action_dispatch = ActionDispatchAgent()
    planner = ChatbotPlannerAgent(cost_monitor)
    executor = ChatbotResponseExecutorAgent(cost_monitor)
    reflector = ChatbotReflectorAgent()

    # Register all seven nodes via BaseAgent.as_node() so timing / error-to-
    # state-field wrapping is applied uniformly without each class needing its
    # own try/except.
    graph.add_node("guardrail", guardrail.as_node())
    graph.add_node("memory_agent", memory_agent.as_node())
    graph.add_node("intent_classifier", intent_classifier.as_node())
    graph.add_node("action_dispatch", action_dispatch.as_node())
    graph.add_node("planner", planner.as_node())
    graph.add_node("executor", executor.as_node())
    graph.add_node("reflector", reflector.as_node())

    graph.set_entry_point("guardrail")

    # Guardrail → memory (or short-circuit to END on rejection).
    graph.add_conditional_edges("guardrail", guardrail_router, {"rejected": END, "passed": "memory_agent"})

    # Linear forward path from memory through to the reflector.
    graph.add_edge("memory_agent", "intent_classifier")
    graph.add_edge("intent_classifier", "action_dispatch")
    graph.add_edge("action_dispatch", "planner")
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", "reflector")

    # Reflector loops back to executor only (not to intent_classifier or
    # action_dispatch, which would re-classify the same message and re-fetch
    # the same grounding data for no benefit).
    graph.add_conditional_edges("reflector", reflector_router, {"revise": "executor", "done": END})

    compiled = graph.compile()
    logger.info("agent_graph_compiled", feature="chatbot", nodes=7)
    return compiled


async def run_chat_turn_pipeline(
    *,
    user_id: str,
    raw_input: str,
    session_snapshot: dict[str, Any],
    long_term_memory: dict[str, dict[str, Any]],
    user_context_snapshot: dict[str, Any],
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Run one full chatbot turn — one user message in, one assistant reply
    out — through the 7-node pipeline.

    Parameters
    ----------
    user_id:
        The authenticated user's UUID string.
    raw_input:
        The raw text of the user's new message (sanitized by the
        ChatbotGuardrailAgent inside the graph, not before it).
    session_snapshot:
        ``{"session_id": str, "title": str, "recent_messages": [{"role",
        "content", "created_at"}, ...]}`` — pre-loaded by the route layer
        so the MemoryAgent never touches the database.
    long_term_memory:
        ``{namespace: {key: value}}`` — all ``AgentMemory`` rows for this
        user, flattened into a nested dict by the route layer.
    user_context_snapshot:
        Flat dict summarising the user's current profile/jobs/roadmap/CVs
        built by the route layer before the graph runs.  Keys the
        ActionDispatchAgent relies on include: ``saved_job_count``,
        ``recent_job_titles``, ``active_target_role``,
        ``completed_skill_count``, ``total_skill_count``, ``cv_count``,
        ``profile_completeness``, ``missing_sections``.
    request_id:
        Optional idempotency / trace ID; a fresh UUID hex is generated if
        omitted.

    Returns
    -------
    dict with keys:
        ``state``        — the final merged LangGraph state dict
        ``cost_monitor`` — the ``CostMonitor`` instance (caller persists it)
    """
    cost_monitor = CostMonitor(feature="chatbot")
    graph = _build_chatbot_graph(cost_monitor)

    state = initial_state(
        feature="chatbot",
        user_id=user_id,
        request_id=request_id or uuid.uuid4().hex,
        raw_input=raw_input,
        session_snapshot=session_snapshot,
        long_term_memory=long_term_memory,
        user_context_snapshot=user_context_snapshot,
    )
    final_state = await graph.ainvoke(state)
    raise_if_guardrail_failed(final_state)

    logger.info(
        "chatbot_turn_pipeline_completed",
        intent=final_state.get("intent"),
        confidence=final_state.get("confidence_score"),
        revisions=final_state.get("revision_count", 0),
        memory_updates=len(final_state.get("memory_updates") or []),
        **cost_monitor.summary(),
    )
    return {"state": final_state, "cost_monitor": cost_monitor}
