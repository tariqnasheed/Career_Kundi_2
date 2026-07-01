"""agents/auto_apply/state.py"""
from __future__ import annotations
from typing import Any
from app.agents.common.state import BaseAgentState


class AutoApplyState(BaseAgentState):
    # Input
    job_source_url: str | None
    job_data: dict[str, Any]
    profile_data: dict[str, Any]
    cv_id: str | None
    user_confirmed: bool
    cover_letter_requested: bool
    profile_sufficient: bool

    # Safety
    safety_passed: bool
    safety_issues: list[str]
    platform_blocked: bool
    manual_apply_url: str | None

    # Cover letter
    cover_letter_text: str | None
    cover_letter_generated: bool

    # Form detection
    form_type: str | None
    apply_email: str | None
    can_auto_apply: bool

    # Submission
    apply_status: str
    status_detail: str | None
    platform_confirmation: str | None
    submission_steps: list[dict[str, Any]]

    # Tracker
    tracker_log: list[dict[str, Any]]
    final_status: str | None
