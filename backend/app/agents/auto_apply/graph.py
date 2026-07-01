"""
agents/auto_apply/graph.py
============================
5-node auto-apply pipeline with safety-first design.

Edge logic:
  safety_guard → BLOCKED → END (with manual_apply_url always set)
  safety_guard → PASSED  → cover_letter_agent
  cover_letter_agent → form_detector
  form_detector → can_auto_apply? → submit_agent : tracker_agent (blocked path)
  submit_agent → tracker_agent → END
"""

from __future__ import annotations
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.common.cost_monitor import CostMonitor

from .agents import (
    ApplicationFormDetectorAgent,
    ApplicationSubmitAgent,
    ApplicationTrackerAgent,
    AutoApplySafetyGuard,
    CoverLetterGeneratorAgent,
)
from .state import AutoApplyState


def _build_apply_graph(cost_monitor: CostMonitor) -> Any:
    safety      = AutoApplySafetyGuard()
    cover       = CoverLetterGeneratorAgent(cost_monitor)
    detector    = ApplicationFormDetectorAgent()
    submitter   = ApplicationSubmitAgent()
    tracker     = ApplicationTrackerAgent()

    g = StateGraph(AutoApplyState)
    g.add_node("safety_guard",      safety.run)
    g.add_node("cover_letter",      cover.run)
    g.add_node("form_detector",     detector.run)
    g.add_node("submit",            submitter.run)
    g.add_node("tracker",           tracker.run)

    g.add_edge(START, "safety_guard")
    g.add_conditional_edges(
        "safety_guard",
        lambda s: "cover_letter" if s.get("safety_passed") else "tracker",
    )
    g.add_edge("cover_letter", "form_detector")
    g.add_edge("form_detector", "submit")
    g.add_edge("submit", "tracker")
    g.add_edge("tracker", END)

    return g.compile()


async def run_auto_apply_pipeline(
    *,
    user_id: str,
    job_data: dict,
    profile_data: dict,
    cv_id: str | None,
    user_confirmed: bool,
    cover_letter_requested: bool,
    profile_sufficient: bool,
    request_id: str | None = None,
) -> dict[str, Any]:
    cost_monitor = CostMonitor(feature="auto_apply", user_id=user_id)
    compiled = _build_apply_graph(cost_monitor)

    initial: AutoApplyState = {
        "feature": "auto_apply",
        "user_id": user_id,
        "request_id": request_id or "",
        "raw_input": "",
        "sanitized_input": "",
        "job_source_url": job_data.get("source_url"),
        "job_data": job_data,
        "profile_data": profile_data,
        "cv_id": cv_id,
        "user_confirmed": user_confirmed,
        "cover_letter_requested": cover_letter_requested,
        "profile_sufficient": profile_sufficient,
        "safety_passed": False,
        "safety_issues": [],
        "platform_blocked": False,
        "manual_apply_url": job_data.get("source_url"),
        "cover_letter_text": None,
        "cover_letter_generated": False,
        "form_type": None,
        "apply_email": None,
        "can_auto_apply": False,
        "apply_status": "pending",
        "status_detail": None,
        "platform_confirmation": None,
        "submission_steps": [],
        "tracker_log": [],
        "final_status": None,
        "guardrail_passed": True,
        "guardrail_issues": [],
        "plan": {},
        "draft_output": None,
        "citations": [],
        "retrieved_context": "",
        "search_grounded": False,
        "reflection_issues": [],
        "revision_count": 0,
        "confidence_score": 1.0,
        "model_tier_used": "flash",
    }

    final = await compiled.ainvoke(initial)
    return {"state": final, "cost_monitor": cost_monitor}
