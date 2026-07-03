#!/usr/bin/env python3
"""Non-production helper: capture Iteration 004E-D source ladder integration samples."""

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

from app.agents.job_search.company_research import (
    extract_company_from_html,
    merge_company_research_into_job_snapshot,
    research_to_dict,
)
from app.agents.job_search.job_posting_extractor import (
    extract_job_posting_from_html,
    extraction_to_dict,
    merge_extraction_into_job_snapshot,
)
from app.agents.job_search.knowledge.source_ladder import build_source_ladder_status
from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.answer_length_policy import ABSOLUTE_MAX_WORDS
from app.agents.job_search.quality.blocked_phrase_guard import export_blocked_phrase_count
from app.agents.job_search.quality.silly_question_guard import is_silly_question
from app.tools.document_export import build_interview_pack_markdown

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "project_review" / "samples" / "iteration_004e_d_source_ladder_integration"

JOB_HTML = """
<html><head><script type="application/ld+json">
{"@type":"JobPosting","title":"Data Analyst","description":"Build dashboards.",
 "responsibilities":["SQL dashboard creation","Daily data quality checks"],
 "qualifications":["Strong SQL","Stakeholder communication"],
 "skills":["SQL","Power BI"]}
</script></head></html>
"""

ORG_HTML = """
<html><head><script type="application/ld+json">
{"@type":"Corporation","legalName":"Northline Analytics Ltd","description":"Retail analytics SaaS.",
 "makesOffer":[{"name":"KPI dashboards"}],"knowsAbout":["Retail analytics"]}
</script></head></html>
"""

_URL_RE = re.compile(r"https?://", re.I)
_ROLE_SPECIFIC_RE = re.compile(r"\bRole Specific\b")


def _metrics(job: dict[str, Any], questions: list[dict], pack_md: str) -> dict[str, Any]:
    ladder = (job.get("source_ladder") or {}).get("source_status") or build_source_ladder_status(job)
    audit = job.get("coverage_audit") or {}
    exportable = [q for q in questions if q.get("model_answer") and not q.get("export_blocked")]
    return {
        "user_fields": ladder.get("user_fields"),
        "url_extraction": ladder.get("link_extraction"),
        "company_research": ladder.get("company_research"),
        "model_knowledge": ladder.get("model_knowledge"),
        "document_library": ladder.get("document_library"),
        "local_fallback": ladder.get("local_fallback"),
        "extracted_items": len(audit.get("audit_items") or []),
        "covered_items": audit.get("covered_items", 0),
        "coverage_score": audit.get("coverage_score", "N/A"),
        "added_coverage_questions": audit.get("added_question_count", 0),
        "fake_urls": len(_URL_RE.findall(pack_md)),
        "generic_phrase_hits": export_blocked_phrase_count(pack_md),
        "silly_question_hits": sum(1 for q in exportable if is_silly_question(q.get("question", ""))),
        "internal_label_leaks": len(_ROLE_SPECIFIC_RE.findall(pack_md)),
        "answers_over_500": sum(
            1 for q in exportable if len((q.get("model_answer") or "").split()) > ABSOLUTE_MAX_WORDS
        ),
    }


def _full_ladder_sample() -> dict[str, Any]:
    extraction = extract_job_posting_from_html(JOB_HTML, "https://northline.example/jobs/analyst")
    research = extract_company_from_html(ORG_HTML, "https://northline.example/about")
    job = merge_extraction_into_job_snapshot(
        {
            "title": "Data Analyst",
            "company_name": "Northline Analytics",
            "description_raw": "Build dashboards and KPI reporting.",
            "responsibilities": ["SQL dashboard creation"],
            "requirements": ["Strong SQL", "Excel"],
            "extracted_skills": [{"skill": "SQL"}, {"skill": "Excel"}],
            "company_profile": {"summary": "User boutique analytics consultancy."},
        },
        extraction,
    )
    job = merge_company_research_into_job_snapshot(job, research)
    questions = mock_generate_questions(job, focus_areas=["SQL"], difficulty="mid")
    pack_md = build_interview_pack_markdown(
        job_title=job["title"],
        company_name=job.get("company_name"),
        questions=questions,
    )
    (OUTPUT_DIR / "sample_full_source_ladder_pack.md").write_text(pack_md, encoding="utf-8")
    metrics = _metrics(job, questions, pack_md)
    metrics["sample"] = "Full source ladder"
    return metrics


def _url_company_sample() -> dict[str, Any]:
    extraction = extract_job_posting_from_html(JOB_HTML, "https://northline.example/jobs/analyst")
    research = extract_company_from_html(ORG_HTML, "https://northline.example/about")
    job = merge_extraction_into_job_snapshot({"title": "Data Analyst", "extracted_skills": [{"skill": "SQL"}]}, extraction)
    job = merge_company_research_into_job_snapshot(job, research)
    questions = mock_generate_questions(job, focus_areas=["SQL"], difficulty="mid")
    pack_md = build_interview_pack_markdown(job_title="Data Analyst", company_name="Northline Analytics", questions=questions)
    (OUTPUT_DIR / "sample_url_plus_company_research_pack.md").write_text(pack_md, encoding="utf-8")
    metrics = _metrics(job, questions, pack_md)
    metrics["sample"] = "URL + company research"
    return metrics


def _document_library_sample() -> dict[str, Any]:
    job = {
        "title": "Barista",
        "company_name": "Harbour Cafe",
        "description_raw": "Espresso preparation, milk steaming, and rush-hour customer service.",
        "responsibilities": [
            "Espresso preparation and milk steaming during peak service",
            "HACCP hygiene controls and allergen handling",
        ],
        "requirements": ["Coffee preparation", "Customer service", "HACCP"],
        "extracted_skills": [
            {"skill": "Coffee Preparation"},
            {"skill": "HACCP"},
            {"skill": "Customer Service"},
        ],
    }
    questions = mock_generate_questions(
        job,
        focus_areas=["Coffee Preparation", "HACCP"],
        difficulty="mid",
    )
    pack_md = build_interview_pack_markdown(
        job_title="Barista",
        company_name="Harbour Cafe",
        questions=questions,
    )
    (OUTPUT_DIR / "sample_document_library_source_pack.md").write_text(pack_md, encoding="utf-8")
    metrics = _metrics(job, questions, pack_md)
    metrics["sample"] = "Document library role"
    return metrics


def _title_only_sample() -> dict[str, Any]:
    job = {"title": "Mystery Role"}
    questions = mock_generate_questions(job, focus_areas=[], difficulty="auto")
    pack_md = build_interview_pack_markdown(job_title="Mystery Role", company_name=None, questions=questions)
    (OUTPUT_DIR / "sample_title_only_limited_pack.md").write_text(pack_md, encoding="utf-8")
    metrics = _metrics(job, questions, pack_md)
    metrics["sample"] = "Title only"
    return metrics


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [
        _full_ladder_sample(),
        _url_company_sample(),
        _document_library_sample(),
        _title_only_sample(),
    ]

    extraction = extract_job_posting_from_html(JOB_HTML, "https://northline.example/jobs/analyst")
    full_job = {
        "title": "Data Analyst",
        "responsibilities": ["SQL dashboard creation"],
        "requirements": ["Strong SQL"],
        "extracted_skills": [{"skill": "SQL"}],
        "job_posting_extraction": extraction_to_dict(extraction),
        "company_research": research_to_dict(extract_company_from_html(ORG_HTML, "https://northline.example/about")),
    }
    mock_generate_questions(full_job, focus_areas=["SQL"], difficulty="mid")
    audit_items = (full_job.get("coverage_audit") or {}).get("audit_items") or []
    (OUTPUT_DIR / "sample_coverage_audit_source_items.json").write_text(
        json.dumps(audit_items[:20], indent=2),
        encoding="utf-8",
    )

    (OUTPUT_DIR / "metrics.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")

    lines = [
        "# Iteration 004E-D Source Ladder Integration Summary",
        "",
        f"*Captured: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        "## Implementation notes",
        "",
        "- Full 6-tier source ladder integrated into interview-pack generation.",
        "- Priority: user fields → URL extraction → company research → model knowledge → document library → local fallback.",
        "- No new direct network fetching in 004E-D; reuses 004E-B/004E-C metadata only.",
        "- Model knowledge remains disabled by default.",
        "- 004F global job search remains deferred.",
        "",
        "## Sample metrics",
        "",
        "| Sample | User Fields | URL Extraction | Company Research | Model Knowledge | Document Library | Local Fallback | Extracted Items | Covered Items | Coverage Score | Added Questions | Fake URLs | Generic Hits | Silly Hits | Internal Label Leaks |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['sample']} | {row.get('user_fields')} | {row.get('url_extraction')} | "
            f"{row.get('company_research')} | {row.get('model_knowledge')} | {row.get('document_library')} | "
            f"{row.get('local_fallback')} | {row.get('extracted_items', 0)} | "
            f"{row.get('covered_items', 0)} | {row.get('coverage_score', 'N/A')} | "
            f"{row.get('added_coverage_questions', 0)} | {row.get('fake_urls', 0)} | "
            f"{row.get('generic_phrase_hits', 0)} | {row.get('silly_question_hits', 0)} | "
            f"{row.get('internal_label_leaks', 0)} |"
        )
    lines.extend([
        "",
        "## Quality gates",
        "",
        "Network import scan (004E-D must not add direct fetching outside 004E-B/004E-C):",
        "",
        "```bash",
        "grep -R -E \"(^|\\\\s)(import httpx|import requests|from httpx|from requests|import urllib\\\\.request|from urllib\\\\.request import|urllib\\\\.request\\\\.urlopen|urlopen\\\\()\" -n backend/app/agents/job_search \\\\",
        "  --exclude-dir=\"__pycache__\" \\\\",
        "  --exclude=\"*.pyc\" \\\\",
        "  --exclude=\"test_*\" \\\\",
        "  | grep -v \"job_posting_extractor.py\" \\\\",
        "  | grep -v \"company_research.py\" || true",
        "```",
        "",
        "## Risk controls",
        "",
        "- User fields are never overwritten by weaker extracted/company/document/fallback data.",
        "- No fake URLs, citations, or fabricated company facts.",
        "- Tests use mocked HTML only — no live internet.",
        "",
    ])
    (OUTPUT_DIR / "iteration_004e_d_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote samples to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
