#!/usr/bin/env python3
"""Non-production helper: capture Iteration 004E-A job intelligence foundation samples."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ.setdefault("JOB_SEARCH_ENABLE_MODEL_KNOWLEDGE", "false")
os.environ.setdefault("JOB_SEARCH_MODEL_KNOWLEDGE_PROVIDER", "disabled")

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.agents.job_search.job_intelligence import build_job_intelligence_profile, profile_summary_text
from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.answer_length_policy import ABSOLUTE_MAX_WORDS
from app.agents.job_search.quality.blocked_phrase_guard import export_blocked_phrase_count
from app.agents.job_search.quality.silly_question_guard import is_silly_question
from app.services.role_pack_library import build_role_overview
from app.tools.document_export import build_interview_pack_markdown

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "project_review" / "samples" / "iteration_004e_job_intelligence_foundation"

SCENARIOS: list[dict[str, Any]] = [
    {
        "slug": "role_title_only_data_analyst",
        "label": "Data Analyst (title only)",
        "title": "Data Analyst",
        "job": {"title": "Data Analyst"},
    },
    {
        "slug": "rich_job_posting_data_analyst",
        "label": "Data Analyst (rich posting)",
        "title": "Data Analyst",
        "job": {
            "title": "Data Analyst",
            "company_name": "Northline Analytics",
            "description_raw": (
                "Northline Analytics builds subscription analytics products for retail brands.\n\n"
                "Responsibilities:\n"
                "- Build SQL dashboards and KPI definitions for stakeholder reporting\n"
                "- Run daily data quality checks on warehouse tables\n"
                "- Partner with finance on Excel and Power BI reporting\n\n"
                "Requirements:\n"
                "- Strong SQL querying and dashboard creation\n"
                "- Experience with data quality checks and stakeholder communication\n"
                "- Preferred: Python for automation"
            ),
            "responsibilities": [
                "SQL querying and dashboard creation for stakeholder reporting",
                "Daily data quality checks on warehouse tables",
                "KPI definitions and executive reporting",
            ],
            "requirements": [
                "Strong SQL querying and dashboard creation",
                "Experience with data quality checks",
                "Preferred: Python for automation",
            ],
            "extracted_skills": [
                {"skill": "SQL", "importance": "critical"},
                {"skill": "Power BI", "importance": "high"},
            ],
            "company_profile": {
                "summary": "Retail subscription analytics SaaS provider",
                "industry": "Retail analytics",
                "products_services": "Subscription analytics dashboards",
            },
            "location": "Manchester, UK",
        },
    },
    {
        "slug": "rich_job_posting_electrical_engineer",
        "label": "Electrical Engineer (rich posting)",
        "title": "Electrical Engineer",
        "job": {
            "title": "Electrical Engineer",
            "company_name": "GridForm Projects",
            "description_raw": (
                "Support LV distribution design, load calculations, cable sizing, site inspections, "
                "AutoCAD drawings, testing/commissioning, and electrical safety compliance."
            ),
            "responsibilities": [
                "LV distribution design support and load calculations",
                "Cable sizing and protective device coordination",
                "Site inspections, testing, and commissioning",
            ],
            "requirements": [
                "AutoCAD design experience",
                "Electrical safety and standards compliance",
                "Commissioning and inspection records",
            ],
            "extracted_skills": [{"skill": "AutoCAD", "importance": "critical"}],
            "company_profile": {
                "summary": "Commercial electrical contractor",
                "industry": "Construction",
            },
        },
    },
    {
        "slug": "rich_job_posting_social_media_creator",
        "label": "Social Media Creator (rich posting)",
        "title": "Social Media Creator",
        "job": {
            "title": "Social Media Creator",
            "company_name": "BrightLoop Media",
            "description_raw": (
                "Own the content calendar, short-form video production, audience growth analytics, "
                "brand safety reviews, sponsorship awareness, copyright checks, and community management."
            ),
            "responsibilities": [
                "Plan and publish the weekly content calendar",
                "Produce short-form video and hooks for audience growth",
                "Review analytics and community feedback daily",
                "Apply brand safety and copyright checks before publishing",
            ],
            "requirements": [
                "Short-form video editing",
                "Analytics and audience growth reporting",
                "Brand safety and sponsorship awareness",
            ],
            "extracted_skills": [
                {"skill": "Content Planning", "importance": "critical"},
                {"skill": "Analytics", "importance": "high"},
            ],
            "company_profile": {
                "summary": "Creator-led media studio",
                "products_services": "Short-form video campaigns",
                "industry": "Digital media",
            },
        },
    },
]

_URL_RE = re.compile(r"https?://", re.I)


def _coverage_score_display(audit: dict[str, Any], extracted_items: int) -> str:
    if extracted_items == 0 or audit.get("total_items", 0) == 0:
        return "N/A"
    return str(audit.get("coverage_score", 0))


def _analyze(job: dict[str, Any], questions: list[dict], pack_md: str, *, slug: str, label: str) -> dict[str, Any]:
    profile = build_job_intelligence_profile(job)
    exportable = [q for q in questions if not q.get("export_blocked") and q.get("model_answer")]
    audit = job.get("coverage_audit") or {}
    return {
        "slug": slug,
        "sample": label,
        "completeness_score": profile.completeness_score,
        "extracted_items": len(profile.extracted_items),
        "covered_items": audit.get("covered_items", 0),
        "coverage_score": audit.get("coverage_score", 0),
        "coverage_score_display": _coverage_score_display(audit, len(profile.extracted_items)),
        "added_coverage_questions": audit.get("added_question_count", 0),
        "warnings": len(profile.warnings),
        "generic_phrase_hits": export_blocked_phrase_count(pack_md),
        "silly_question_hits": sum(1 for q in exportable if is_silly_question(q.get("question", ""))),
        "fake_urls": len(_URL_RE.findall(pack_md)),
        "answers_over_500": sum(
            1 for q in exportable if len((q.get("model_answer") or "").split()) > ABSOLUTE_MAX_WORDS
        ),
        "questions": len(exportable),
        "profile_summary": profile_summary_text(profile),
        "warning_examples": profile.warnings,
        "audit_warnings": audit.get("warnings", []),
        "source_status": profile.source_status,
        "low_input": len(profile.extracted_items) == 0,
    }


def _example_added_question(job: dict[str, Any], questions: list[dict]) -> str:
    for q in questions:
        meta = q.get("generation_stage_meta") or {}
        if meta.get("stage_4_coverage_audit"):
            return q.get("question", "")
    for q in questions:
        meta = q.get("generation_stage_meta") or {}
        if meta.get("profile_driven"):
            return q.get("question", "")
    return questions[0]["question"] if questions else ""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    metrics: list[dict[str, Any]] = []
    example_warning = ""
    example_profile = ""
    example_audit = ""
    example_added = ""

    for scenario in SCENARIOS:
        job = dict(scenario["job"])
        skills = [s["skill"] for s in job.get("extracted_skills", []) if isinstance(s, dict)]
        questions = mock_generate_questions(job, focus_areas=skills, difficulty="mid")
        overview = build_role_overview(scenario["title"], job)
        pack_md = build_interview_pack_markdown(
            job_title=scenario["title"],
            company_name=job.get("company_name"),
            questions=questions,
            role_overview=overview,
        )
        out_path = OUTPUT_DIR / f"{scenario['slug']}.md"
        out_path.write_text(pack_md, encoding="utf-8")
        row = _analyze(
            job,
            questions,
            pack_md,
            slug=scenario["slug"],
            label=scenario.get("label", scenario["title"]),
        )
        metrics.append(row)
        if scenario["slug"] == "role_title_only_data_analyst":
            if row["warning_examples"]:
                example_warning = row["warning_examples"][0]
        if scenario["slug"] == "rich_job_posting_data_analyst":
            example_profile = row["profile_summary"]
            audit = job.get("coverage_audit") or {}
            example_audit = (
                f"Coverage score {audit.get('coverage_score', 0)}/100 — "
                f"{audit.get('covered_items', 0)}/{audit.get('total_items', 0)} items covered; "
                f"added {audit.get('added_question_count', 0)} coverage questions."
            )
            example_added = _example_added_question(job, questions)
        print(
            f"Wrote {out_path.name}: questions={row['questions']} "
            f"coverage={row['coverage_score_display']}"
        )

    (OUTPUT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    summary_lines = [
        "# Iteration 004E-A Job Intelligence Foundation Summary",
        "",
        f"*Captured: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        "## Goal",
        "",
        "Add Job Intelligence Profile extraction, completeness warnings, coverage audit, and "
        "missing-coverage question generation without live web research or model API calls.",
        "",
        "## 004E-A-S stabilization",
        "",
        "- Fixed generic-phrase metric false positives (`role specification` no longer counts as the internal category label).",
        "- Empty/title-only profiles now report coverage score `0` / summary `N/A` with an explicit audit warning.",
        "- Summary labels distinguish title-only vs rich posting samples.",
        "",
        "## 004E-A changes",
        "",
        "- Added `job_intelligence.py` with deterministic `JobIntelligenceProfile` builder.",
        "- Added `job_coverage_audit.py` with coverage audit and missing-item question generation.",
        "- Integrated profile-driven questions and audit fill in `mock_generate_questions()`.",
        "- Added `silly_question_guard.py` to block filler/vague questions on rich profiles.",
        "- Extended `InterviewPackRead` with `job_intelligence` and `coverage_audit` metadata.",
        "",
        "## Sample metrics",
        "",
        "| Sample | Completeness Score | Extracted Items | Covered Items | Coverage Score | Added Coverage Questions | Warnings | Generic Phrase Hits | Silly Question Hits | Fake URLs | Answers Over 500 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    title_only_row = next((m for m in metrics if m.get("slug") == "role_title_only_data_analyst"), None)
    for m in metrics:
        summary_lines.append(
            f"| {m['sample']} | {m['completeness_score']} | {m['extracted_items']} | {m['covered_items']} | "
            f"{m['coverage_score_display']} | {m['added_coverage_questions']} | {m['warnings']} | "
            f"{m['generic_phrase_hits']} | {m['silly_question_hits']} | {m['fake_urls']} | {m['answers_over_500']} |"
        )

    if title_only_row:
        audit_warn = (title_only_row.get("audit_warnings") or [None])[0] or ""
        summary_lines.extend(
            [
                "",
                "## Title-only sample notes",
                "",
                f"- Completeness score is low ({title_only_row['completeness_score']}/100).",
                "- No detailed job intelligence items were extracted from the input.",
                f"- Coverage audit is limited/not meaningful (coverage score: {title_only_row['coverage_score_display']}).",
                f"- Audit warning: {audit_warn}" if audit_warn else "- Audit warning: none captured.",
                "- Generation continues using local deterministic fallback and role-title baseline questions.",
                f"- Source status: user fields `{title_only_row['source_status'].get('user_fields', 'thin')}`, "
                f"local fallback `{title_only_row['source_status'].get('local_fallback', 'used')}`.",
            ]
        )

    summary_lines.extend(
        [
            "",
            "## Example completeness warning",
            "",
            example_warning or "_No warning captured._",
            "",
            "## Example Job Intelligence Profile summary",
            "",
            example_profile or "_No profile summary captured._",
            "",
            "## Example coverage audit summary",
            "",
            example_audit or "_No audit summary captured._",
            "",
            "## Example added missing-coverage question",
            "",
            example_added or "_No added question captured._",
            "",
            "## Remaining for 004E-B",
            "",
            "- Job posting link extraction from user-provided URLs.",
            "- Company web research with real captured URLs only (no fake citations).",
            "- Source-cited company profile capture.",
            "- Frontend extracted-field review/edit UI before generation.",
            "",
        ]
    )
    (OUTPUT_DIR / "iteration_004e_summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    print(f"\nWrote samples to {OUTPUT_DIR.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
