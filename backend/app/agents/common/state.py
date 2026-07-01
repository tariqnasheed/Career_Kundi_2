"""
agents/common/state.py
==========================
`BaseAgentState`: the common state shape threaded through every LangGraph
pipeline in the platform.

Why a shared TypedDict
-----------------------
LangGraph's `StateGraph` is parameterized by a state schema (commonly a
`TypedDict`), and every node receives/returns (partial updates of) that
schema. Each feature defines its OWN state TypedDict — e.g.
`app/agents/job_search/state.py::JobSearchState` — that extends this base
with domain-specific fields (the job URL, the parsed job fields, the
interview pack draft, etc.). Because TypedDicts support inheritance, the
shared Guardrail/Reflector/graph_utils code in this package can be written
once against `BaseAgentState`'s keys and works identically no matter which
feature's (wider) state dict actually flows through it at runtime.
"""

from __future__ import annotations

from typing import Any, TypedDict


class BaseAgentState(TypedDict, total=False):
    """
    Common keys read/written by the shared framework. `total=False` means
    every key is optional — a freshly-started pipeline run only needs to
    set `feature`, `user_id`, and whichever input field the Guardrail
    reads; everything else is populated as the pipeline progresses.
    """

    # --- Identity / request context -----------------------------------------
    user_id: str
    feature: str  # "job_search" | "cv_builder" | "roadmap" | "chatbot"
    request_id: str

    # --- Guardrail stage -----------------------------------------------------
    guardrail_passed: bool
    guardrail_issues: list[str]

    # --- Planner stage ---------------------------------------------------------
    plan: dict[str, Any]

    # --- Executor stage -----------------------------------------------------------
    draft_output: Any
    citations: list[dict[str, Any]]
    retrieved_context: str
    search_grounded: bool

    # --- Reflector stage ------------------------------------------------------------
    reflection_passed: bool
    reflection_forced_accept: bool
    reflection_issues: list[str]
    confidence_score: float
    revision_count: int
    _should_revise: bool

    # --- Cost / audit ---------------------------------------------------------------
    total_prompt_tokens: int
    total_completion_tokens: int
    model_tier_used: str

    # --- Terminal --------------------------------------------------------------------
    final_output: Any
    error: str | None
