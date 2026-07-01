"""
agents/job_extractor/graph.py
================================
4-node LangGraph pipeline for URL-based job import:

  START → guardrail → scraper → extractor → reflector → END

If guardrail fails, we short-circuit directly to END with
`guardrail_passed=False` so the route can return a 422 with the issues.

If scrape_success is False (page blocked / empty) we set
`extraction_incomplete=True` and return what we have so the user sees
the editable manual-entry form.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.common.cost_monitor import CostMonitor

from .agents import (
    JobExtractionReflectorAgent,
    JobFieldExtractorAgent,
    JobPageScraperAgent,
    JobURLGuardrailAgent,
)
from .state import JobExtractorState


def _build_extractor_graph(cost_monitor: CostMonitor) -> Any:
    guardrail  = JobURLGuardrailAgent()
    scraper    = JobPageScraperAgent()
    extractor  = JobFieldExtractorAgent(cost_monitor)
    reflector  = JobExtractionReflectorAgent(cost_monitor)

    graph = StateGraph(JobExtractorState)
    graph.add_node("guardrail",  guardrail.run)
    graph.add_node("scraper",    scraper.run)
    graph.add_node("extractor",  extractor.run)
    graph.add_node("reflector",  reflector.run)

    graph.add_edge(START, "guardrail")
    graph.add_conditional_edges(
        "guardrail",
        lambda s: "scraper" if s.get("guardrail_passed") else END,
    )
    graph.add_edge("scraper", "extractor")
    graph.add_conditional_edges(
        "extractor",
        lambda s: "reflector" if s.get("scrape_success") else END,
    )
    # Reflector may loop back for one revision pass (minor field corrections)
    graph.add_conditional_edges(
        "reflector",
        lambda s: (
            "extractor"
            if (s.get("revision_count", 0) < 1 and s.get("reflection_issues"))
            else END
        ),
    )

    return graph.compile()


async def run_job_extraction_pipeline(
    *,
    user_id: str,
    job_url: str,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Run the full URL extraction pipeline.

    Returns
    -------
    {
        "state":        final LangGraph state dict,
        "cost_monitor": CostMonitor instance (for route-layer persist())
    }
    """
    cost_monitor = CostMonitor(feature="job_extractor", user_id=user_id)
    compiled = _build_extractor_graph(cost_monitor)

    initial_state: JobExtractorState = {
        "feature":        "job_extractor",
        "user_id":        user_id,
        "request_id":     request_id or "",
        "raw_input":      job_url,
        "sanitized_input": job_url,
        "job_url":        job_url,
        "guardrail_passed": False,
        "guardrail_issues": [],
        "scrape_success": False,
        "raw_page_text": None,
        "extracted_fields": {},
        "extraction_incomplete": True,
        "missing_fields": [],
        "source_url": None,
        "citations": [],
        "retrieved_context": "",
        "search_grounded": False,
        "draft_output": None,
        "plan": {},
        "reflection_issues": [],
        "revision_count": 0,
        "confidence_score": 1.0,
        "model_tier_used": "flash",
    }

    final_state = await compiled.ainvoke(initial_state)
    return {"state": final_state, "cost_monitor": cost_monitor}
