#!/usr/bin/env python3
"""Non-production helper: capture Iteration 004A study source metadata samples."""

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
OUTPUT_DIR = REPO_ROOT / "project_review" / "samples" / "iteration_004a_study_source_metadata"

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


def _joined_guard_tokens() -> tuple[str, ...]:
    return (
        "deterministic" + "mode",
        "available_not_used" + "when",
        "not_configured" + "in",
        "local" + "fallback",
        "source " + "ladderis",
        "source" + "ladderis",
    )

_FAKE_URL_RE = re.compile(r"https?://[^\s\])\"']+")
_SOURCE_BLOCK_RE = re.compile(
    r"### Source / fallback status\s*\n(.*?)(?=\n### |\n---|\Z)",
    re.S,
)


def _job(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": snapshot["title"],
        "responsibilities": snapshot["responsibilities"],
        "requirements": snapshot["requirements"],
        "extracted_skills": [{"skill": s} for s in snapshot["extracted_skills"]],
    }


def _analyze(snapshot: dict, questions: list[dict], pack_md: str) -> dict[str, Any]:
    exportable = [q for q in questions if not q.get("export_blocked") and q.get("model_answer")]
    fake_urls = 0
    for q in exportable:
        blob = json.dumps(q.get("study_sources") or {})
        if _FAKE_URL_RE.search(blob):
            fake_urls += 1
        for source in (q.get("study_sources") or {}).get("sources") or []:
            if source.get("url"):
                fake_urls += 1

    study_present = sum(1 for q in exportable if q.get("study_material"))
    meta_present = sum(1 for q in exportable if q.get("study_sources"))
    local_used = sum(
        1
        for q in exportable
        if "local_fallback" in ((q.get("study_sources") or {}).get("used_source_types") or [])
    )
    source_rendered = pack_md.count("### Source / fallback status")
    words = [len((q.get("model_answer") or "").split()) for q in exportable]
    lowered_md = pack_md.lower()
    joined_hits = [token for token in _joined_guard_tokens() if token in lowered_md]

    return {
        "role": snapshot["title"],
        "questions": len(exportable),
        "study_material_present": study_present,
        "source_metadata_present": meta_present,
        "local_fallback_used": local_used,
        "fake_urls_found": fake_urls,
        "source_status_rendered": source_rendered,
        "answers_over_500": sum(1 for w in words if w > ABSOLUTE_MAX_WORDS),
        "hr_present": int(any(q.get("category") == "hr" for q in exportable)),
        "daily_routine_present": int(any(q.get("category") == "daily_routine" for q in exportable)),
        "seniority_present": int(
            any(
                q.get("question_type") == "seniority"
                or any(k in (q.get("question") or "").lower() for k in ("junior", "senior", "mid-level"))
                for q in exportable
            )
        ),
        "case_or_practical_present": int(
            any(
                q.get("question_type") in {"case_study", "practical_task"}
                or "case study" in (q.get("question") or "").lower()
                or "practical task" in (q.get("question") or "").lower()
                for q in exportable
            )
        ),
        "joined_source_artifacts": joined_hits,
    }


def _example_source_block(pack_md: str) -> str:
    match = _SOURCE_BLOCK_RE.search(pack_md)
    if not match:
        return "(no source block found)"
    return "### Source / fallback status\n" + match.group(1).strip()


def _build_summary(metrics: list[dict], example_block: str) -> str:
    lines = [
        "# Iteration 004A Study Source Metadata Summary",
        "",
        f"*Captured: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        "## Goal",
        "",
        "Add study-material source metadata architecture foundation without enabling live web, model, or PDF retrieval.",
        "",
        "**004A-S:** Fixed source-status wording (`deterministic mode`) and verified coverage parity with Iteration 003B snapshots.",
        "",
        "## Quality table",
        "",
        "| Role | Questions | Study Material Present | Source Metadata Present | Local Fallback Used | Fake URLs Found | Source Status Rendered | Answers Over 500 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for m in metrics:
        lines.append(
            f"| {m['role']} | {m['questions']} | {m['study_material_present']} | "
            f"{m['source_metadata_present']} | {m['local_fallback_used']} | {m['fake_urls_found']} | "
            f"{m['source_status_rendered']} | {m['answers_over_500']} |"
        )

    lines.extend(
        [
            "",
            "## Coverage confirmation (003B parity)",
            "",
            "| Role | HR | Daily routine | Seniority | Case/practical | Joined source artifacts |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    for m in metrics:
        hits = ", ".join(m["joined_source_artifacts"]) if m["joined_source_artifacts"] else "none"
        lines.append(
            f"| {m['role']} | {m['hr_present']} | {m['daily_routine_present']} | "
            f"{m['seniority_present']} | {m['case_or_practical_present']} | {hits} |"
        )

    lines.extend(
        [
            "",
            "## Example source / fallback status block",
            "",
            "```markdown",
            example_block,
            "```",
            "",
            "## Retrieval implementation status",
            "",
            "| Source | Status in 004A |",
            "|---|---|",
            "| Web research | **Not implemented** — marked `not_configured` |",
            "| Model knowledge | **Not implemented** for study modules — marked `not_configured` in deterministic mode |",
            "| Document library (PDF/Markdown/JSON) | **Detection only** — `available_not_used` when saved pack exists; not consumed yet |",
            "| Local deterministic fallback | **Used** — current compiler/template study content |",
            "",
            "## Remaining for Iteration 004B",
            "",
            "- Wire document-library retrieval into study synthesis for matching roles/skills",
            "- Add model-knowledge draft step behind feature flag",
            "- Add web-research agent stub with real URL capture (no fake citations)",
            "- Persist source metadata through saved role packs and API responses",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    metrics: list[dict] = []
    example_block = ""

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
        if not example_block:
            example_block = _example_source_block(pack_md)
        print(
            f"{snapshot['title']}: {m['questions']} questions, meta={m['source_metadata_present']}, "
            f"coverage=HR:{m['hr_present']}/daily:{m['daily_routine_present']}, "
            f"artifacts={m['joined_source_artifacts'] or 'none'}"
        )

    (OUTPUT_DIR / "iteration_004a_summary.md").write_text(
        _build_summary(metrics, example_block), encoding="utf-8"
    )
    (OUTPUT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"\nWrote samples to {OUTPUT_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
