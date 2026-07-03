#!/usr/bin/env python3
"""Non-production helper: capture Iteration 004E-E study material finalization samples."""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
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
)
from app.agents.job_search.job_posting_extractor import (
    extract_job_posting_from_html,
    merge_extraction_into_job_snapshot,
)
from app.agents.job_search.knowledge.question_study_material import (
    count_empty_study_sections,
    study_module_fingerprint,
)
from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.answer_length_policy import ABSOLUTE_MAX_WORDS
from app.agents.job_search.quality.blocked_phrase_guard import export_blocked_phrase_count
from app.tools.document_export import build_interview_pack_markdown

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "project_review" / "samples" / "iteration_004e_e_study_material_finalization"

JOB_HTML = """
<html><head><script type="application/ld+json">
{"@type":"JobPosting","title":"Data Analyst","description":"Build dashboards.",
 "responsibilities":["SQL dashboard creation","Daily data quality checks"],
 "tools":["Power BI","SQL"],"skills":["SQL","Python"]}
</script></head></html>
"""

ORG_HTML = """
<html><head><script type="application/ld+json">
{"@type":"Corporation","legalName":"Northline Analytics Ltd",
 "makesOffer":[{"name":"KPI dashboards"}],"knowsAbout":["Retail analytics"]}
</script></head></html>
"""

_URL_RE = re.compile(r"https?://", re.I)
_INTERNAL_LABEL_RE = re.compile(r"\bRole Specific\b")


def _exportable(questions: list[dict]) -> list[dict]:
    return [q for q in questions if q.get("model_answer") and not q.get("export_blocked")]


def _study_blob(questions: list[dict]) -> str:
    parts: list[str] = []
    for q in questions:
        study = q.get("study_material") or {}
        for value in study.values():
            if isinstance(value, str):
                parts.append(value)
            elif isinstance(value, list):
                parts.extend(str(v) for v in value if v)
    return " ".join(parts)


def _metrics(questions: list[dict], pack_md: str) -> dict[str, Any]:
    exportable = _exportable(questions)
    studies = [q.get("study_material") or {} for q in exportable]
    fingerprints = [
        study_module_fingerprint(s, q.get("question") or "") for q, s in zip(exportable, studies)
    ]
    dup_count = sum(c - 1 for c in Counter(fingerprints).values() if c > 1)
    empty_sections = sum(count_empty_study_sections(s) for s in studies)
    source_aware = sum(
        1 for s in studies if s.get("source_items_used") or s.get("source_types_used")
    )
    question_specific = sum(1 for s in studies if s.get("what_this_question_tests") and s.get("question_text"))
    doc_insights = sum(1 for s in studies if s.get("document_library_insight"))
    blob = _study_blob(exportable) + " " + pack_md
    return {
        "question_count": len(exportable),
        "study_module_count": len(studies),
        "missing_study_module_count": len(exportable) - len(studies),
        "question_specific_module_count": question_specific,
        "source_aware_module_count": source_aware,
        "document_insight_count": doc_insights,
        "model_status": "disabled",
        "fake_url_hits": len(_URL_RE.findall(blob)),
        "generic_phrase_hits": export_blocked_phrase_count(blob),
        "empty_section_count": empty_sections,
        "duplicate_module_count": dup_count,
        "internal_label_leak_count": len(_INTERNAL_LABEL_RE.findall(blob)),
        "answers_over_500": sum(
            1 for q in exportable if len((q.get("model_answer") or "").split()) > ABSOLUTE_MAX_WORDS
        ),
    }


def _full_ladder_job() -> dict:
    extraction = extract_job_posting_from_html(JOB_HTML, "https://northline.example/jobs/analyst")
    research = extract_company_from_html(ORG_HTML, "https://northline.example/about")
    job = merge_extraction_into_job_snapshot(
        {
            "title": "Data Analyst",
            "company_name": "Northline Analytics",
            "description_raw": "Build dashboards and KPI reporting.",
            "responsibilities": ["SQL dashboard creation"],
            "requirements": ["Strong SQL"],
            "extracted_skills": [{"skill": "SQL"}, {"skill": "Excel"}],
        },
        extraction,
    )
    return merge_company_research_into_job_snapshot(job, research)


def _run_sample(name: str, job: dict, focus: list[str], outfile: str) -> dict[str, Any]:
    questions = mock_generate_questions(job, focus_areas=focus, difficulty="mid")
    exportable = _exportable(questions)
    pack_md = build_interview_pack_markdown(
        job_title=job.get("title") or "Role",
        company_name=job.get("company_name"),
        questions=exportable,
    )
    (OUTPUT_DIR / outfile).write_text(pack_md, encoding="utf-8")
    metrics = _metrics(exportable, pack_md)
    metrics["sample"] = name
    return metrics


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = [
        _run_sample("Full source ladder", _full_ladder_job(), ["SQL"], "sample_full_source_ladder_study_material.md"),
        _run_sample(
            "Question-specific modules",
            _full_ladder_job(),
            ["SQL"],
            "sample_question_specific_modules.md",
        ),
        _run_sample(
            "Document library",
            {
                "title": "Barista",
                "company_name": "Harbour Cafe",
                "description_raw": "Espresso and HACCP hygiene.",
                "responsibilities": ["Espresso preparation", "HACCP hygiene controls"],
                "requirements": ["Coffee preparation", "HACCP"],
                "extracted_skills": [{"skill": "Coffee Preparation"}, {"skill": "HACCP"}],
            },
            ["Coffee Preparation", "HACCP"],
            "sample_document_library_study_material.md",
        ),
        _run_sample(
            "Title only fallback",
            {"title": "Mystery Role"},
            [],
            "sample_title_only_fallback_study_material.md",
        ),
    ]

    export_job = _full_ladder_job()
    export_qs = _exportable(mock_generate_questions(export_job, focus_areas=["SQL"], difficulty="mid"))
    export_md = build_interview_pack_markdown(
        job_title="Data Analyst",
        company_name="Northline Analytics",
        questions=export_qs,
    )
    (OUTPUT_DIR / "sample_export_ready_interview_pack_study_material.md").write_text(export_md, encoding="utf-8")

    (OUTPUT_DIR / "metrics.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")

    lines = [
        "# Iteration 004E-E Study Material Finalization Summary",
        "",
        f"*Captured: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        "## Implementation notes",
        "",
        "- Every exportable interview question receives a dedicated study module.",
        "- Study modules use 004E-D source-ladder metadata (question source items/types/priority).",
        "- Model knowledge remains disabled by default; no live web/model calls in samples.",
        "- 004F global job search remains deferred; role catalog not implemented.",
        "- Final Content Library Regeneration not run in this phase.",
        "",
        "## Risk controls",
        "",
        "- No whole-role generic study notes; each module ties to the exact question.",
        "- No fake URLs, citations, or invented company facts.",
        "- User-provided values remain highest priority in the source ladder.",
        "",
        "## Sample metrics",
        "",
        "| Sample | Questions | Study Modules | Missing Study Modules | Question-Specific Modules | Source-Aware Modules | Document Insights | Model Status | Fake URLs | Generic Hits | Empty Sections | Duplicate Modules | Internal Label Leaks |",
        "|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['sample']} | {row.get('question_count', 0)} | {row.get('study_module_count', 0)} | "
            f"{row.get('missing_study_module_count', 0)} | {row.get('question_specific_module_count', 0)} | "
            f"{row.get('source_aware_module_count', 0)} | {row.get('document_insight_count', 0)} | "
            f"{row.get('model_status', 'disabled')} | {row.get('fake_url_hits', 0)} | "
            f"{row.get('generic_phrase_hits', 0)} | {row.get('empty_section_count', 0)} | "
            f"{row.get('duplicate_module_count', 0)} | {row.get('internal_label_leak_count', 0)} |"
        )
    lines.extend([
        "",
        "## Quality gates",
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
    ])
    (OUTPUT_DIR / "iteration_004e_e_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote samples to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
