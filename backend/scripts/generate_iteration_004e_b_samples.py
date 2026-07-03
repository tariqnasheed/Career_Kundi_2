#!/usr/bin/env python3
"""Non-production helper: capture Iteration 004E-B job posting URL extraction samples."""

from __future__ import annotations

import asyncio
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
from app.agents.job_search.job_posting_extractor import (
    enrich_job_snapshot_from_posting_url,
    extract_job_posting_from_html,
    extraction_to_dict,
    merge_extraction_into_job_snapshot,
)
from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.answer_length_policy import ABSOLUTE_MAX_WORDS
from app.agents.job_search.quality.blocked_phrase_guard import export_blocked_phrase_count
from app.agents.job_search.quality.silly_question_guard import is_silly_question
from app.services.role_pack_library import build_role_overview
from app.tools.document_export import build_interview_pack_markdown

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "project_review" / "samples" / "iteration_004e_b_job_posting_extraction"

JSON_LD_HTML = """
<html><head><script type="application/ld+json">
{
  "@type": "JobPosting",
  "title": "Data Analyst",
  "description": "Build dashboards and KPI reporting for retail analytics clients.",
  "hiringOrganization": {"name": "Northline Analytics", "description": "Retail subscription analytics SaaS"},
  "jobLocation": {"address": {"addressLocality": "Manchester", "addressCountry": "UK"}},
  "employmentType": "FULL_TIME",
  "responsibilities": ["SQL dashboard creation", "Daily data quality checks", "KPI definitions"],
  "qualifications": ["Strong SQL", "Stakeholder communication", "Preferred: Python automation"],
  "skills": ["SQL", "Power BI", "Python"]
}
</script></head><body></body></html>
"""

HTML_FALLBACK = """
<html><body>
<h2>Responsibilities</h2><ul><li>Prepare espresso drinks</li><li>Maintain cleanliness standards</li></ul>
<h2>Requirements</h2><ul><li>Customer service experience</li><li>Food safety awareness</li></ul>
<h2>Preferred qualifications</h2><ul><li>Latte art experience</li></ul>
<h2>Tools</h2><ul><li>POS systems</li></ul>
</body></html>
"""

_URL_RE = re.compile(r"https?://", re.I)


def _field_count(extraction: dict[str, Any]) -> int:
    count = 0
    for key in ("title", "company_name", "description", "location", "employment_type"):
        if extraction.get(key):
            count += 1
    for list_key in ("responsibilities", "requirements", "skills", "tools"):
        count += len(extraction.get(list_key) or [])
    return count


def _analyze_pack(job: dict[str, Any], questions: list[dict], pack_md: str) -> dict[str, Any]:
    profile = build_job_intelligence_profile(job)
    exportable = [q for q in questions if not q.get("export_blocked") and q.get("model_answer")]
    audit = job.get("coverage_audit") or {}
    return {
        "extracted_field_count": _field_count(job.get("job_posting_extraction") or {}),
        "responsibilities_extracted": len(profile.responsibilities),
        "requirements_extracted": len(profile.required_skills) + len(profile.preferred_skills),
        "skills_extracted": len(profile.required_skills) + len(profile.technical_skills),
        "tools_extracted": len(profile.tools_software),
        "warnings_count": len(profile.warnings),
        "coverage_score": audit.get("coverage_score", 0),
        "added_coverage_questions": audit.get("added_question_count", 0),
        "fake_urls": len(_URL_RE.findall(pack_md)),
        "generic_phrase_hits": export_blocked_phrase_count(pack_md),
        "silly_question_hits": sum(1 for q in exportable if is_silly_question(q.get("question", ""))),
        "answers_over_500": sum(
            1 for q in exportable if len((q.get("model_answer") or "").split()) > ABSOLUTE_MAX_WORDS
        ),
        "questions": len(exportable),
        "profile_summary": profile_summary_text(profile),
    }


async def _build_json_ld_sample() -> dict[str, Any]:
    extraction = extract_job_posting_from_html(JSON_LD_HTML, "https://example.com/jobs/data-analyst")
    job = merge_extraction_into_job_snapshot({"title": "Data Analyst"}, extraction)
    questions = mock_generate_questions(job, focus_areas=[], difficulty="auto")
    overview = build_role_overview(job["title"], job)
    pack_md = build_interview_pack_markdown(
        job_title=job["title"],
        company_name=job.get("company_name"),
        questions=questions,
        role_overview=overview,
    )
    payload = {
        "extraction": extraction_to_dict(extraction),
        "merged_job": {k: v for k, v in job.items() if k != "job_intelligence_profile"},
        "pack_metrics": _analyze_pack(job, questions, pack_md),
    }
    (OUTPUT_DIR / "sample_json_ld_job_posting_extraction.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "sample_interview_pack_from_mocked_url.md").write_text(pack_md, encoding="utf-8")
    return {
        "sample": "JSON-LD JobPosting",
        "extraction_method": ",".join(extraction.extraction_methods),
        "confidence": extraction.extraction_confidence,
        "extracted_fields": _field_count(extraction_to_dict(extraction)),
        "warnings": len(extraction.warnings),
        **payload["pack_metrics"],
    }


async def _build_html_fallback_sample() -> dict[str, Any]:
    extraction = extract_job_posting_from_html(HTML_FALLBACK, "https://example.com/jobs/barista")
    job = merge_extraction_into_job_snapshot({"title": "Barista"}, extraction)
    questions = mock_generate_questions(job, focus_areas=[], difficulty="auto")
    pack_md = build_interview_pack_markdown(job_title="Barista", company_name=None, questions=questions)
    payload = {
        "extraction": extraction_to_dict(extraction),
        "merged_job": {k: v for k, v in job.items() if k != "job_intelligence_profile"},
        "pack_metrics": _analyze_pack(job, questions, pack_md),
    }
    (OUTPUT_DIR / "sample_html_fallback_extraction.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    return {
        "sample": "HTML section fallback",
        "extraction_method": ",".join(extraction.extraction_methods),
        "confidence": extraction.extraction_confidence,
        "extracted_fields": _field_count(extraction_to_dict(extraction)),
        "warnings": len(extraction.warnings),
        **payload["pack_metrics"],
    }


async def _build_manual_merge_sample() -> dict[str, Any]:
    merged, extraction = await enrich_job_snapshot_from_posting_url(
        {
            "title": "Data Analyst",
            "company_name": "User Override Corp",
            "requirements": ["User-listed stakeholder communication skill"],
            "source_url": "https://example.com/jobs/data-analyst",
        },
        html=JSON_LD_HTML,
    )
    assert extraction is not None
    lines = [
        "# Manual fields + URL extraction merge",
        "",
        "## User-provided (preserved)",
        "- Title: Data Analyst",
        "- Company: User Override Corp",
        "- Requirement: User-listed stakeholder communication skill",
        "",
        "## Extracted from mocked URL (filled gaps)",
        f"- Company from URL (ignored): {extraction.company_name}",
        f"- Responsibilities added: {len(merged.get('responsibilities') or [])}",
        f"- Skills added: {len(merged.get('extracted_skills') or [])}",
        f"- Confidence: {extraction.extraction_confidence}",
        "",
        "## Merge rule",
        "User-provided fields remain highest priority; extracted URL content fills missing responsibilities, skills, and description.",
    ]
    (OUTPUT_DIR / "sample_manual_plus_url_merge.md").write_text("\n".join(lines), encoding="utf-8")
    return {
        "sample": "Manual + URL merge",
        "extraction_method": ",".join(extraction.extraction_methods),
        "confidence": extraction.extraction_confidence,
        "extracted_fields": _field_count(extraction_to_dict(extraction)),
        "warnings": len(extraction.warnings),
        "user_company_preserved": merged.get("company_name") == "User Override Corp",
    }


async def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [
        await _build_json_ld_sample(),
        await _build_html_fallback_sample(),
        await _build_manual_merge_sample(),
    ]
    (OUTPUT_DIR / "metrics.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")

    summary_lines = [
        "# Iteration 004E-B Job Posting Link Extraction Summary",
        "",
        f"*Captured: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        "## Implementation notes",
        "",
        "- JSON-LD Schema.org `JobPosting` is parsed first when present.",
        "- HTML heading/section fallback is used when structured data is missing.",
        "- User-provided manual fields override extracted URL fields.",
        "- Tests use mocked/static HTML — no live internet required.",
        "- Live URL fetch uses manual redirect validation, DNS/IP SSRF checks, and a 2 MB response cap.",
        "- 004F global job search remains deferred.",
        "",
        "### Future improvements (deferred)",
        "",
        "- Cache extraction result on saved job / pack generation to avoid repeated live fetches.",
        "- Optional robots.txt compliance check before fetch.",
        "- Persist merged extraction fields on saved job rows when useful.",
        "",
        "## Sample metrics",
        "",
        "| Sample | Extraction Method | Confidence | Extracted Fields | Warnings | Coverage Score | Added Coverage Questions | Fake URLs | Generic Phrase Hits | Silly Question Hits |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        summary_lines.append(
            f"| {row['sample']} | {row.get('extraction_method', '')} | {row.get('confidence', '')} | "
            f"{row.get('extracted_fields', 0)} | {row.get('warnings', 0)} | "
            f"{row.get('coverage_score', 'N/A')} | {row.get('added_coverage_questions', 0)} | "
            f"{row.get('fake_urls', 0)} | {row.get('generic_phrase_hits', 0)} | {row.get('silly_question_hits', 0)} |"
        )
    summary_lines.extend(
        [
            "",
            "## Research-assisted development",
            "",
            "- Primary structured source: Schema.org JobPosting JSON-LD (`application/ld+json`).",
            "- Fallback: OpenGraph/meta tags and HTML section headings (Responsibilities, Requirements, etc.).",
            "- SSRF safety: no automatic redirects; each hop validated; private/loopback/link-local IPs blocked.",
            "- No fake URLs or fabricated extraction content.",
            "",
        ]
    )
    (OUTPUT_DIR / "iteration_004e_b_summary.md").write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"Wrote samples to {OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
