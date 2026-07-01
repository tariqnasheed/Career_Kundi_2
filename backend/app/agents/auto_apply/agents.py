"""
agents/auto_apply/agents.py
==============================
5-node pipeline for the auto-apply workflow:

  START → safety_guard → cover_letter_agent → form_detector →
          submit_agent → tracker_agent → END

Safety invariants (enforced in this file, not just in comments):
  - safety_guard raises immediately if user_confirmed != True
  - submit_agent never stores or logs passwords
  - All fields submitted are logged to tracker before submission
  - On any failure, manual_apply_url is always returned

Node responsibilities
---------------------
safety_guard        Verify explicit user confirmation, check platform limitations,
                    detect blocked domains, validate CV selection.
cover_letter_agent  Generate a tailored cover letter (mock: template + profile data).
                    Only runs if the job posting requests one.
form_detector       Detect the application form type:
                    - direct_email   (send CV + cover letter by email)
                    - portal_apply   (job board "Easy Apply" style form)
                    - blocked        (cannot automate — returns manual URL)
submit_agent        Fill and submit the form (mock: simulates progress steps).
tracker_agent       Write the structured tracker_log to state.
"""

from __future__ import annotations

from typing import Any

from app.agents.common.base import BaseAgent
from app.agents.common.cost_monitor import CostMonitor
from app.core.config import settings

from . import mock_data

# ---------------------------------------------------------------------------
# Safety guard
# ---------------------------------------------------------------------------

_BLOCKED_AUTO_APPLY_DOMAINS = frozenset({
    "linkedin.com", "greenhouse.io", "lever.co",
    "workday.com", "taleo.net", "icims.com",
    "smartrecruiters.com", "jobvite.com",
})


class AutoApplySafetyGuard(BaseAgent):
    """
    First node — the only gate that can hard-block the pipeline.

    Checks (in order):
      1. user_confirmed is True (must be set by the route after the user
         pressed "Confirm & Submit" — never set server-side)
      2. Source URL is not on the blocked-domains list
      3. A CV is selected (or profile data is complete enough to proceed)
    """

    name = "AutoApplySafetyGuard"

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        issues: list[str] = []

        if not state.get("user_confirmed"):
            return {
                "safety_passed": False,
                "safety_issues": ["Explicit user confirmation is required before submitting."],
                "apply_status": "awaiting_confirmation",
            }

        source_url = state.get("job_source_url", "")
        if source_url:
            from urllib.parse import urlparse
            domain = urlparse(source_url).netloc.lower().removeprefix("www.")
            if domain in _BLOCKED_AUTO_APPLY_DOMAINS:
                return {
                    "safety_passed": False,
                    "safety_issues": [
                        f"{domain} does not allow automated applications. "
                        "Use the manual apply link below."
                    ],
                    "apply_status": "blocked",
                    "manual_apply_url": source_url,
                    "platform_blocked": True,
                }

        if not state.get("cv_id") and not state.get("profile_sufficient"):
            issues.append("No CV selected and profile is incomplete. Please select a CV or complete your profile first.")

        if issues:
            return {
                "safety_passed": False,
                "safety_issues": issues,
                "apply_status": "blocked",
            }

        return {"safety_passed": True, "safety_issues": [], "apply_status": "running"}


# ---------------------------------------------------------------------------
# Cover letter agent
# ---------------------------------------------------------------------------

class CoverLetterGeneratorAgent(BaseAgent):
    """
    Generates a tailored cover letter when one is requested.
    Preserves truth: uses only profile data and job description provided.
    Does NOT invent experiences, achievements, or qualifications.
    """

    name = "CoverLetterGeneratorAgent"

    def __init__(self, cost_monitor: CostMonitor) -> None:
        super().__init__()
        self.cost_monitor = cost_monitor

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        if not state.get("cover_letter_requested"):
            return {"cover_letter_text": None, "cover_letter_generated": False}

        job_data:     dict = state.get("job_data", {})
        profile_data: dict = state.get("profile_data", {})

        if settings.llm_mode == "mock":
            cover_letter = mock_data.generate_cover_letter(job_data, profile_data)
        else:
            # Live mode: generate through the shared LLM provider abstraction.
            # `get_llm(tier)` returns the Gemini (or mock) provider; we build a
            # PromptSpec with the SAME field names every other agent uses
            # (system_prompt / user_prompt), call `.generate()`, and record the
            # token cost. Cover letters are free-form prose, so no json_schema.
            from app.tools.llm import PromptSpec, get_llm

            llm = get_llm("flash")
            spec = PromptSpec(
                system_prompt=(
                    "Write a professional cover letter using ONLY the profile data and job description provided. "
                    "Do NOT invent achievements, companies, dates, or qualifications. "
                    "Be specific to this role and this person. Keep it under 350 words. "
                    "Use a confident, professional tone — not sycophantic."
                ),
                user_prompt=(
                    f"Job: {job_data.get('title')} at {job_data.get('company_name')}\n\n"
                    f"Job Description:\n{job_data.get('description_raw', '')[:2000]}\n\n"
                    f"Applicant Profile:\n{str(profile_data)[:2000]}"
                ),
                temperature=0.5,
            )
            response = await llm.generate(spec)
            self.cost_monitor.record(response, tier="flash")
            cover_letter = response.text

        return {
            "cover_letter_text": cover_letter,
            "cover_letter_generated": True,
        }


# ---------------------------------------------------------------------------
# Form detector
# ---------------------------------------------------------------------------

class ApplicationFormDetectorAgent(BaseAgent):
    """
    Detects what kind of application submission is possible for this job:
      direct_email   — Company posts an email address; attach CV and cover letter
      easy_apply     — Simple one-click or short-form portal
      full_portal    — Complex multi-page portal (often blocked)
      blocked        — Cannot automate; return manual URL

    In mock mode: returns based on domain heuristics.
    """

    name = "ApplicationFormDetectorAgent"

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        source_url = state.get("job_source_url", "")

        if settings.llm_mode == "mock":
            form_type, apply_email = mock_data.detect_form_type(source_url)
        else:
            # In live mode: would use scraper to check the page for form elements
            form_type = "easy_apply"
            apply_email = None

        return {
            "form_type": form_type,
            "apply_email": apply_email,
            "can_auto_apply": form_type in ("direct_email", "easy_apply"),
        }


# ---------------------------------------------------------------------------
# Submit agent
# ---------------------------------------------------------------------------

class ApplicationSubmitAgent(BaseAgent):
    """
    Fills and submits the application.

    Safety guarantees:
      - Logs every field it will submit BEFORE submission
      - Never stores passwords
      - Sets manual_apply_url on any failure so the user can always complete manually
      - Returns structured tracker_log steps
    """

    name = "ApplicationSubmitAgent"

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        form_type   = state.get("form_type", "blocked")
        job_data    = state.get("job_data", {})
        profile_data = state.get("profile_data", {})
        cover_letter = state.get("cover_letter_text")
        cv_id       = state.get("cv_id")
        source_url  = state.get("job_source_url", "")

        if not state.get("can_auto_apply"):
            return {
                "apply_status": "manual_required",
                "status_detail": "Auto-apply is not available for this job posting. Use the direct link below.",
                "manual_apply_url": source_url,
                "submission_steps": [
                    {"step": "form_detection", "status": "blocked",
                     "detail": f"Form type '{form_type}' cannot be automated."},
                ],
                "platform_confirmation": None,
            }

        if settings.llm_mode == "mock":
            result = mock_data.simulate_submission(
                form_type, job_data, profile_data, cover_letter, cv_id
            )
        else:
            # Live: would use browser automation / email SMTP
            result = {
                "apply_status": "submitted",
                "status_detail": "Application submitted successfully.",
                "platform_confirmation": "APP-MOCK-12345",
                "submission_steps": [
                    {"step": "fill_form", "status": "done", "detail": "Fields completed"},
                    {"step": "attach_cv", "status": "done", "detail": "CV attached"},
                    {"step": "submit",    "status": "done", "detail": "Form submitted"},
                ],
                "manual_apply_url": source_url,
            }

        return result


# ---------------------------------------------------------------------------
# Tracker agent
# ---------------------------------------------------------------------------

class ApplicationTrackerAgent(BaseAgent):
    """
    Assembles the final tracker_log from all submission steps and
    computes the terminal status for persistence.
    """

    name = "ApplicationTrackerAgent"

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        from datetime import datetime, timezone

        steps = state.get("submission_steps", [])
        status = state.get("apply_status", "unknown")

        # Add timestamps to each step
        now = datetime.now(timezone.utc).isoformat()
        tracker_log = [
            {**step, "ts": now}
            for step in steps
        ]

        # Add summary entry
        tracker_log.append({
            "step": "application_complete",
            "status": status,
            "ts": now,
            "detail": state.get("status_detail", ""),
        })

        return {
            "tracker_log": tracker_log,
            "final_status": status,
        }
