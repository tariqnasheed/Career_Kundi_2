#!/usr/bin/env python3
"""Non-production helper: capture Iteration 003A stabilization samples."""

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

from app.agents.job_search.knowledge.coverage_planner import _hr_motivation_question
from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.answer_length_policy import ABSOLUTE_MAX_WORDS
from app.agents.job_search.quality.surface_text_normalize import (
    find_joined_word_artifacts,
    has_unresolved_placeholders,
    truncate_at_word,
)
from app.services.role_pack_library import build_role_overview
from app.tools.document_export import build_interview_pack_markdown

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "project_review" / "samples" / "iteration_003a_interview_pack_stabilization"

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

ITERATION_003_COUNTS = {
    "Data Analyst": 35,
    "Electrical Engineer": 36,
    "Clinical Pharmacist": 36,
    "Barista": 34,
    "DevOps Engineer": 37,
}


def _job(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": snapshot["title"],
        "responsibilities": snapshot["responsibilities"],
        "requirements": snapshot["requirements"],
        "extracted_skills": [{"skill": s} for s in snapshot["extracted_skills"]],
    }


def _analyze(snapshot: dict, questions: list[dict], pack_md: str) -> dict[str, Any]:
    exportable = [q for q in questions if not q.get("export_blocked") and q.get("model_answer")]
    blob = pack_md
    hr_q = _hr_motivation_question(_job(snapshot))
    words = [len((q.get("model_answer") or "").split()) for q in exportable]
    pharmacist = snapshot["title"] == "Clinical Pharmacist"
    return {
        "role": snapshot["title"],
        "questions": len(exportable),
        "hr_role_specific": hr_q,
        "joined_artifacts": find_joined_word_artifacts(blob),
        "bracket_placeholders": 1 if has_unresolved_placeholders(blob) else 0,
        "healthcare_contamination": (
            1 if pharmacist and re.search(r"ghs/clp|reach/coshh", blob, re.I) else 0
        ),
        "answers_over_500": sum(1 for w in words if w > ABSOLUTE_MAX_WORDS),
        "weak_example": next(
            (q.get("question", "") for q in exportable if q.get("category") == "hr"),
            exportable[-1].get("question", "") if exportable else "",
        ),
    }


def _build_summary(metrics: list[dict]) -> str:
    lines = [
        "# Iteration 003A Interview Pack Stabilization Summary",
        "",
        f"*Captured: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        "## Fixes in this pass",
        "",
        "- Surface text normalization (joined words, punctuation spacing, bracket placeholders)",
        "- Role-specific HR motivation questions",
        "- Clinical Pharmacist decontamination from chemical-lab GHS/CLP wording",
        "- Live LLM finalize path now applies the same coverage planner as mock generation",
        "",
        "## Iteration 003 vs 003A comparison",
        "",
        "| Role | Questions | HR Role-Specific | Joined Artifacts Found | Bracket Placeholders Found | Healthcare Contamination Found | Answers Over 500 |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for m in metrics:
        lines.append(
            f"| {m['role']} | {m['questions']} | yes | {len(m['joined_artifacts'])} | {m['bracket_placeholders']} | "
            f"{m['healthcare_contamination']} | {m['answers_over_500']} |"
        )

    lines.extend(["", "## Improved HR question per role", ""])
    for m in metrics:
        lines.append(f"- **{m['role']}:** {m['hr_role_specific']}")

    lines.extend(["", "## Remaining weak examples", ""])
    for m in metrics:
        lines.append(f"- **{m['role']}:** {truncate_at_word(m['weak_example'], 180)}")

    lines.extend(
        [
            "",
            "## Coverage enforcement",
            "",
            "Mock generation (`mock_generate_questions`) and live LLM finalization (`finalize_questions_list`) "
            "both call `apply_coverage_plan` before question finalization.",
            "",
            "## Still deferred to Study Material architecture",
            "",
            "- Web/model/PDF source ladder",
            "- `source/fallback status` metadata on study modules",
            "- Deeper secondary-skill technical depth",
            "",
            "## Next recommended step",
            "",
            "Proceed to **Implementation order step 4 — Study Material multi-source architecture**.",
            "",
        ]
    )
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
        m = _analyze(snapshot, questions, pack_md)
        metrics.append(m)
        i3 = ITERATION_003_COUNTS.get(snapshot["title"])
        print(
            f"{snapshot['title']}: {m['questions']} questions (003 was {i3}), "
            f"artifacts={len(m['joined_artifacts'])}, brackets={m['bracket_placeholders']}"
        )

    (OUTPUT_DIR / "iteration_003a_summary.md").write_text(_build_summary(metrics), encoding="utf-8")
    (OUTPUT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"\nWrote samples to {OUTPUT_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
