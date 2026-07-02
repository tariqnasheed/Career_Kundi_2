"""
agents/job_search/graph.py
===============================
Pipeline entry points for the Job Search & Discovery (§4.1) and Interview
Pack Generation (§4.2) features. Route handlers in
`app/api/routes/job_search.py` call ONLY `run_job_enrichment_pipeline()`
and `run_interview_pack_pipeline()` — every LangGraph/agent detail is
encapsulated here.

Design note — scraping happens BEFORE the graph runs
------------------------------------------------------
Resolving "URL or pasted text" down to plain job-posting text is treated as
a pre-pipeline concern, not a Guardrail/Planner responsibility: scraping
success/failure is about external-system availability, not input safety or
planning. If `scrape_job_posting()` can't get usable content, we raise
immediately with a clear "paste the text instead" error rather than ever
entering the agent graph with nothing to work on — this is what keeps the
zero-hallucination guarantee intact even when the scraper fails.
"""

from __future__ import annotations

import uuid
from typing import Any
from urllib.parse import urlparse

from app.agents.common.cost_monitor import CostMonitor
from app.agents.common.graph_utils import build_revision_pipeline, initial_state
from app.agents.common.guardrail import raise_if_guardrail_failed
from app.core.errors import ScrapingFailedError
from app.core.logging import get_logger
from app.tools.scraper import scrape_job_posting

from .agents import (
    CrossVerifierAgent,
    InterviewPackExecutorAgent,
    InterviewPackGuardrailAgent,
    InterviewPackPlannerAgent,
    InterviewPackReflectorAgent,
    JobEnricherExecutorAgent,
    JobPlannerAgent,
    JobReflectorAgent,
    JobSearchGuardrailAgent,
)
from .state import InterviewPackState, JobEnrichmentState

logger = get_logger(__name__)


async def run_job_enrichment_pipeline(
    *,
    user_id: str,
    url: str | None = None,
    pasted_text: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Resolve a URL or pasted job description into structured, RAG-grounded,
    cross-verified job fields. Raises `ScrapingFailedError` (mapped to the
    standard error envelope by the global exception handler) if a given
    URL cannot be scraped — the caller should then prompt the user to
    paste the description text directly instead of retrying blindly.
    """
    if url:
        scrape_result = await scrape_job_posting(url)
        if scrape_result.needs_manual_input:
            raise ScrapingFailedError(
                scrape_result.error or "Could not extract content from this URL.",
                details={"url": url},
            )
        job_text = scrape_result.description_text
        source_meta = {
            "source_url": url,
            "source_site": urlparse(url).netloc or None,
            "import_method": "pasted_url",
        }
    elif pasted_text:
        job_text = pasted_text
        source_meta = {"source_url": None, "source_site": None, "import_method": "manual"}
    else:
        raise ValueError("Either url or pasted_text must be provided.")

    cost_monitor = CostMonitor(feature="job_search")
    graph = build_revision_pipeline(
        guardrail=JobSearchGuardrailAgent(),
        planner=JobPlannerAgent(cost_monitor),
        executor=JobEnricherExecutorAgent(cost_monitor),
        reflector=JobReflectorAgent(),
        state_schema=JobEnrichmentState,
        extra_nodes={"cross_verifier": CrossVerifierAgent()},
        executor_to_reflector_via="cross_verifier",
    )

    state = initial_state(
        feature="job_search",
        user_id=user_id,
        request_id=request_id or uuid.uuid4().hex,
        raw_input=job_text,
        source_kind="text",
    )
    final_state = await graph.ainvoke(state)
    raise_if_guardrail_failed(final_state)

    logger.info(
        "job_enrichment_pipeline_completed",
        confidence=final_state.get("confidence_score"),
        revisions=final_state.get("revision_count"),
        **cost_monitor.summary(),
    )

    return {"state": final_state, "cost_monitor": cost_monitor, "source_meta": source_meta}


async def run_interview_pack_pipeline(
    *,
    user_id: str,
    job_snapshot: dict[str, Any],
    focus_areas: list[str] | None = None,
    difficulty: str = "auto",
    include_study_material: bool = True,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Generate an interview pack against an already-enriched job snapshot (a saved job's fields as a plain dict)."""
    cost_monitor = CostMonitor(feature="interview_pack")
    graph = build_revision_pipeline(
        guardrail=InterviewPackGuardrailAgent(),
        planner=InterviewPackPlannerAgent(cost_monitor),
        executor=InterviewPackExecutorAgent(cost_monitor),
        reflector=InterviewPackReflectorAgent(),
        state_schema=InterviewPackState,
    )

    raw_input_text = f"{job_snapshot.get('title', '')}\n{job_snapshot.get('description_raw') or ''}"
    state = initial_state(
        feature="interview_pack",
        user_id=user_id,
        request_id=request_id or uuid.uuid4().hex,
        raw_input=raw_input_text,
        job_snapshot=job_snapshot,
        focus_areas=focus_areas or [],
        difficulty=difficulty,
        include_study_material=include_study_material,
    )
    final_state = await graph.ainvoke(state)
    raise_if_guardrail_failed(final_state)

    logger.info(
        "interview_pack_pipeline_completed",
        num_questions=len((final_state.get("draft_output") or {}).get("questions", [])),
        confidence=final_state.get("confidence_score"),
        **cost_monitor.summary(),
    )

    return {"state": final_state, "cost_monitor": cost_monitor}
