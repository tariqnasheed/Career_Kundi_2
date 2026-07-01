"""
agents/chatbot/state.py
============================
State shape for the AI Assistant Chatbot's per-turn pipeline (§4.7).

A chatbot "turn" is one user message in (already persisted as a `ChatMessage`
row by the route layer before the graph runs) and one assistant reply out.
Unlike the other three features, this pipeline has no DB-backed draft to
revise across multiple HTTP calls — it runs once per message, end to end,
inside a single `run_chat_turn_pipeline()` call.

Per the platform-wide invariant that agents never touch the database
directly, every piece of persisted context this pipeline needs (recent
conversation history, cross-session long-term memory, a flattened snapshot
of the user's profile/jobs/roadmaps/CVs) is loaded by `app/api/routes/
chatbot.py` BEFORE the graph runs and handed in as plain dicts via
`session_snapshot` / `long_term_memory` / `user_context_snapshot`. Anything
this pipeline decides should be remembered long-term comes back out as
`memory_updates`, which the route layer upserts into `AgentMemory` AFTER
the graph finishes — the same "route layer persists, agents only propose"
split used by every other feature's CostMonitor.persist() call.

Extends `BaseAgentState` so the shared Guardrail/Reflector/graph_utils code
operates on it without modification.
"""

from __future__ import annotations

from typing import Any

from app.agents.common.state import BaseAgentState


class ChatbotConversationState(BaseAgentState, total=False):
    # --- Input (set by run_chat_turn_pipeline, vetted by ChatbotGuardrailAgent) ---
    raw_input: str  # the new user message text
    session_snapshot: dict[str, Any]  # {"session_id", "title", "recent_messages": [{"role","content","created_at"}, ...]}
    long_term_memory: dict[str, dict[str, Any]]  # namespace -> {key: value}, flattened from AgentMemory rows
    user_context_snapshot: dict[str, Any]  # flattened User/Profile/SavedJob/Roadmap/GeneratedCV summary

    # --- MemoryAgent stage ---
    memory_context: str  # compact text digest of long_term_memory + recent history, used to ground the reply prompt
    memory_updates: list[dict[str, Any]]  # proposed AgentMemory upserts: [{"namespace", "key", "value"}], persisted by the route layer

    # --- IntentClassifierAgent stage ---
    intent: str  # general_question | job_search_guidance | cv_feedback | roadmap_guidance | profile_help | action_request | smalltalk
    intent_confidence: float

    # --- ActionDispatchAgent stage ---
    action_taken: str | None  # short label describing what grounding data was actually gathered, e.g. "fetched_saved_jobs_summary"
    action_result: dict[str, Any]  # structured grounding payload handed to the Executor and stored on ChatMessage.action_result

    # --- Planner / Executor stage ---
    persona_directive: str  # tone/style steering derived from chat_preferences memory, if any

    # --- ActionDispatchAgent transient grounding handles passed to the Executor ---
    # Populated by ActionDispatchAgent from the top RAG result; consumed by
    # ChatbotResponseExecutorAgent in mock mode to produce a grounded, citation-
    # annotated reply without an LLM call. Declared here explicitly so LangGraph
    # doesn't silently drop them during the node-to-node state merge.
    source_sentence: str | None  # first sentence of top retrieved RAG document
    citation_marker: int | None  # the [n] index the source_sentence is cited as (always 1)

    # --- Final reply (draft_output shape: {"reply": str, "suggested_followups": list[str]}) ---
