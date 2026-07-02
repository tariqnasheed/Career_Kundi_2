#!/usr/bin/env python3
"""Non-production helper: capture Iteration 003 interview-pack samples after coverage fixes."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.answer_length_policy import ABSOLUTE_MAX_WORDS
from app.services.role_pack_library import build_role_overview
from app.tools.document_export import build_interview_pack_markdown

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "project_review" / "samples" / "iteration_003_interview_pack_fix"
BASELINE_DIR = REPO_ROOT / "project_review" / "samples" / "iteration_002_baseline"

ROLE_SNAPSHOTS: list[dict[str, Any]] = [
    {
        "slug": "data_analyst",
        "title": "Data Analyst",
        "primary_skill": "SQL",
        "responsibilities": [
            "SQL querying and dashboard creation for stakeholder reporting",
            "Data cleaning, data quality checks, and KPI/metrics reporting",
            "Query performance tuning and validation of analytical outputs",
            "Excel or BI tool delivery for recurring business reviews",
        ],
        "requirements": [
            "SQL querying", "dashboard creation", "stakeholder reporting", "data cleaning",
            "data quality checks", "query performance", "KPI/metrics reporting", "Excel or BI tools",
        ],
        "extracted_skills": ["SQL", "Data Quality", "Dashboarding", "Excel"],
    },
    {
        "slug": "electrical_engineer",
        "title": "Electrical Engineer",
        "primary_skill": "Electrical Installation",
        "responsibilities": [
            "LV distribution design support and load calculations",
            "Cable sizing, lighting/power layout review, and site coordination",
            "Testing, commissioning, electrical safety, and standards compliance",
        ],
        "requirements": [
            "LV distribution", "load calculations", "cable sizing", "lighting or power layout review",
            "testing and commissioning", "electrical safety", "standards/compliance", "site coordination",
        ],
        "extracted_skills": ["Electrical Installation", "Load Calculations", "Cable Sizing", "Commissioning"],
    },
    {
        "slug": "clinical_pharmacist",
        "title": "Clinical Pharmacist",
        "primary_skill": "Pharmacology",
        "responsibilities": [
            "Medication review, prescribing safety, and patient counselling",
            "Clinical documentation, escalation, and governance in multidisciplinary teams",
            "Risk management for high-risk medicines and care transitions",
        ],
        "requirements": [
            "medication review", "prescribing safety", "patient counselling", "clinical documentation",
            "escalation", "governance", "multidisciplinary working", "risk management",
        ],
        "extracted_skills": ["Pharmacology", "Medication Review", "Patient Counselling", "Clinical Governance"],
    },
    {
        "slug": "barista",
        "title": "Barista",
        "primary_skill": "Coffee Preparation",
        "responsibilities": [
            "Espresso preparation, milk steaming, and drink consistency during rush hours",
            "Hygiene, allergen controls, customer service, and stock handling",
        ],
        "requirements": [
            "espresso preparation", "milk steaming", "drink consistency", "hygiene",
            "allergens", "customer service", "speed during rush hours", "stock handling",
        ],
        "extracted_skills": ["Coffee Preparation", "HACCP", "Customer Service", "Stock Control"],
    },
    {
        "slug": "devops_engineer",
        "title": "DevOps Engineer",
        "primary_skill": "AWS",
        "responsibilities": [
            "AWS infrastructure automation with CI/CD, Docker, and Kubernetes",
            "Monitoring, incident response, security controls, and rollback/recovery",
        ],
        "requirements": [
            "AWS", "CI/CD", "Docker", "Kubernetes", "monitoring",
            "incident response", "security", "rollback/recovery", "infrastructure automation",
        ],
        "extracted_skills": ["AWS", "CI/CD", "Docker", "Kubernetes", "Monitoring"],
    },
]

ITERATION_002_COUNTS = {
    "Data Analyst": 29,
    "Electrical Engineer": 28,
    "Clinical Pharmacist": 28,
    "Barista": 24,
    "DevOps Engineer": 32,
}


def _job(snapshot: dict[str, Any]) -> dict[str, Any]:
    skills = snapshot["extracted_skills"]
    return {
        "title": snapshot["title"],
        "responsibilities": snapshot["responsibilities"],
        "requirements": snapshot["requirements"],
        "extracted_skills": [{"skill": skill} for skill in skills],
    }


def _flag(questions: list[dict], category: str | None = None, qtype: str | None = None) -> bool:
    if category:
        return any(q.get("category") == category for q in questions)
    if qtype:
        return any(q.get("question_type") == qtype for q in questions)
    return False


def _analyze(snapshot: dict, questions: list[dict]) -> dict[str, Any]:
    exportable = [q for q in questions if not q.get("export_blocked") and q.get("model_answer")]
    words = [len((q.get("model_answer") or "").split()) for q in exportable]
    return {
        "role": snapshot["title"],
        "questions": len(exportable),
        "hr_present": _flag(exportable, category="hr"),
        "daily_routine_present": _flag(exportable, category="daily_routine"),
        "seniority_present": _flag(exportable, qtype="seniority") or any(
            "senior" in (q.get("question") or "").lower() or "junior" in (q.get("question") or "").lower()
            for q in exportable
        ),
        "case_practical_present": any(
            q.get("question_type") in {"case_study", "practical_task"} for q in exportable
        ),
        "skills_covered_better": len(exportable) > ITERATION_002_COUNTS.get(snapshot["title"], 0),
        "answers_over_500": sum(1 for w in words if w > ABSOLUTE_MAX_WORDS),
        "avg_words": round(sum(words) / len(words), 1) if words else 0,
        "strong_example": exportable[0].get("question", "") if exportable else "",
        "weak_example": next(
            (q.get("question", "") for q in exportable if q.get("category") == "hr"),
            exportable[-1].get("question", "") if exportable else "",
        ),
    }


def _build_summary(metrics: list[dict]) -> str:
    lines = [
        "# Iteration 003 Interview Pack Fix Summary",
        "",
        f"*Captured: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        "## Generation method",
        "",
        "- Script: `backend/scripts/generate_iteration_003_samples.py`",
        "- Functions: `mock_generate_questions`, `apply_coverage_plan`, `build_role_overview`, `build_interview_pack_markdown`",
        "- Production logic changed: **yes** (coverage planner, HR/daily-routine categories, behavioral answer expansion, frontend flow)",
        "",
        "## Iteration 002 vs 003 comparison",
        "",
        "| Role | Iteration 002 Questions | Iteration 003 Questions | HR Present | Daily Routine Present | Seniority Present | Case/Practical Present | Skills Covered Better? | Answers Over 500 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for m in metrics:
        i2 = ITERATION_002_COUNTS.get(m["role"], "?")
        lines.append(
            f"| {m['role']} | {i2} | {m['questions']} | "
            f"{'yes' if m['hr_present'] else 'no'} | {'yes' if m['daily_routine_present'] else 'no'} | "
            f"{'yes' if m['seniority_present'] else 'no'} | {'yes' if m['case_practical_present'] else 'no'} | "
            f"{'yes' if m['skills_covered_better'] else 'no'} | {m['answers_over_500']} |"
        )

    lines.extend([
        "",
        "## What improved",
        "",
        "- Explicit `hr` and `daily_routine` question categories",
        "- Seniority-tier prompts (junior/mid/senior)",
        "- Case-study and practical-task questions",
        "- Tool/software and standards/safety coverage gaps filled",
        "- Behavioral STAR answers expanded (typically 120+ words)",
        "- Popular role selection no longer auto-generates on frontend",
        "- Company name optional for generation",
        "",
        "## What remains weak",
        "",
        "- Study material still deterministic/compiler-only (no source ladder)",
        "- Some HR answers use placeholder brackets for notice period",
        "- Live LLM path may not yet mirror all mock coverage rules",
        "- Frontend download still only in pack preview section",
        "",
        "## Strong question example per role",
        "",
    ])
    for m in metrics:
        lines.append(f"- **{m['role']}:** {m['strong_example'][:160]}…")

    lines.extend(["", "## Still-weak question example per role", ""])
    for m in metrics:
        lines.append(f"- **{m['role']}:** {m['weak_example'][:160]}…")

    lines.extend([
        "",
        "## Next recommended step",
        "",
        "Proceed to **Study Material multi-source architecture** (Implementation order step 4) after validating frontend workflow in manual QA.",
        "",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    metrics: list[dict] = []

    for snapshot in ROLE_SNAPSHOTS:
        job = _job(snapshot)
        focus = [snapshot["primary_skill"]] + [
            s for s in snapshot["extracted_skills"] if s != snapshot["primary_skill"]
        ]
        questions = mock_generate_questions(job, focus_areas=focus, difficulty="mid")
        role_overview = build_role_overview(snapshot["title"], job)
        pack_md = build_interview_pack_markdown(
            job_title=snapshot["title"],
            company_name=None,
            questions=questions,
            role_overview=role_overview,
        )
        path = OUTPUT_DIR / f"{snapshot['slug']}_interview_pack.md"
        path.write_text(pack_md, encoding="utf-8")
        m = _analyze(snapshot, questions)
        metrics.append(m)
        print(f"{snapshot['title']}: {m['questions']} questions (was {ITERATION_002_COUNTS.get(snapshot['title'])})")

    summary = _build_summary(metrics)
    (OUTPUT_DIR / "iteration_003_summary.md").write_text(summary, encoding="utf-8")
    (OUTPUT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"\nWrote samples to {OUTPUT_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
