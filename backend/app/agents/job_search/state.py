"""
agents/job_search/state.py
==============================
State shapes for the two LangGraph pipelines in this feature package:

- `JobEnrichmentState` — Guardrail -> Planner -> Executor -> CrossVerifier ->
  Reflector. Input is a URL or pasted job description; output is the
  structured `JobEnrichmentResult` (see app/schemas/job_search.py).
- `InterviewPackState` — Guardrail -> Planner -> Executor -> Reflector.
  Input is an already-enriched job (a `SavedJob` row, dict-ified); output
  is the open-ended list of interview questions.

Both extend `BaseAgentState` so the shared Guardrail/Reflector/graph_utils
code operates on them without modification.
"""

from __future__ import annotations

from typing import Any

from app.agents.common.state import BaseAgentState


class JobEnrichmentState(BaseAgentState, total=False):
    # --- Input ---
    raw_input: str  # the URL or pasted text — whichever the Guardrail vets
    source_kind: str  # "url" | "pasted_text"

    # --- Planner output ---
    needs_scraping: bool

    # --- Executor intermediate / output ---
    scrape_result: dict[str, Any]  # ScrapeResult.__dict__ if a URL was scraped
    job_text: str  # the final plain-text job description, however it was obtained

    # --- CrossVerifier output ---
    verification_status: str
    verification_sources: list[dict]


class InterviewPackState(BaseAgentState, total=False):
    # --- Input ---
    raw_input: str  # serialized job context the Guardrail vets (title + description)
    job_snapshot: dict[str, Any]  # the SavedJob fields the Executor generates questions from
    focus_areas: list[str]
    difficulty: str
