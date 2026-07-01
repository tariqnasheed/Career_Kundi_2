"""
agents/auto_apply/mock_data.py
================================
Mock helpers for the auto-apply pipeline.
"""

from __future__ import annotations
from urllib.parse import urlparse


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def detect_form_type(source_url: str) -> tuple[str, str | None]:
    """Return (form_type, apply_email)."""
    domain = _domain(source_url)
    if "jobs.google" in domain or "careers.google" in domain:
        return "easy_apply", None
    if "careers.microsoft" in domain:
        return "easy_apply", None
    if "@" in source_url:  # URL contains email hint
        return "direct_email", "careers@example.com"
    # Default: easy_apply for generic domains
    return "easy_apply", None


def generate_cover_letter(job_data: dict, profile_data: dict) -> str:
    title = job_data.get("title", "the role")
    company = job_data.get("company_name", "your company")
    applicant_name = profile_data.get("full_name", "the applicant")
    headline = profile_data.get("professional_headline", "a software engineer")

    return f"""Dear Hiring Manager,

I am writing to express my interest in the {title} position at {company}. As {headline}, I am excited by the opportunity to contribute to your team.

{job_data.get('description_raw', '')[:200].split('.')[0]}. This aligns closely with my experience and the direction I want to take my career.

I have reviewed the requirements for this role carefully and am confident that my background makes me a strong candidate. I would welcome the opportunity to discuss how I can add value to {company}.

Thank you for your consideration.

Kind regards,
{applicant_name}""".strip()


def simulate_submission(
    form_type: str,
    job_data: dict,
    profile_data: dict,
    cover_letter: str | None,
    cv_id: str | None,
) -> dict:
    """Simulate a successful submission with realistic progress steps."""
    steps = []

    if form_type == "direct_email":
        steps = [
            {"step": "compose_email", "status": "done", "detail": "Email composed with CV attachment"},
            {"step": "attach_cv",     "status": "done", "detail": f"CV ({cv_id or 'profile-based'}) attached"},
            {"step": "send_email",    "status": "done", "detail": "Email sent to careers@example.com"},
        ]
        if cover_letter:
            steps.insert(1, {"step": "attach_cover_letter", "status": "done", "detail": "Cover letter attached"})
        return {
            "apply_status": "submitted",
            "status_detail": "Application emailed successfully.",
            "platform_confirmation": None,
            "submission_steps": steps,
            "manual_apply_url": "",
        }

    # easy_apply
    steps = [
        {"step": "open_form",   "status": "done", "detail": "Application form opened"},
        {"step": "fill_fields", "status": "done", "detail": "Name, email, and experience filled"},
        {"step": "attach_cv",   "status": "done", "detail": "CV attached"},
        {"step": "submit",      "status": "done", "detail": "Application submitted"},
    ]
    if cover_letter:
        steps.insert(3, {"step": "add_cover_letter", "status": "done", "detail": "Cover letter added"})

    return {
        "apply_status": "submitted",
        "status_detail": "Application submitted via the job portal.",
        "platform_confirmation": "APP-MOCK-98765",
        "submission_steps": steps,
        "manual_apply_url": "",
    }
