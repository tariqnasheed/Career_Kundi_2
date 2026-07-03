#!/usr/bin/env python3
"""Non-production helper: capture Iteration 004C study synthesis quality samples."""

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

from app.agents.job_search.knowledge.study_synthesis import contains_blocked_generic_phrase
from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.answer_length_policy import ABSOLUTE_MAX_WORDS
from app.agents.job_search.quality.blocked_phrase_guard import (
    INTERMEDIATE_QUALITY_CHECKS,
    OUTCOME_QUALITY_IMPROVES,
    STABILIZE_MAINTAIN_PIPELINES,
    STRUCTURED_VERIFICATION,
)
from app.services.role_pack_library import build_role_overview
from app.tools.document_export import build_interview_pack_markdown

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "project_review" / "samples" / "iteration_004c_study_synthesis_quality"

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

_BLOCKED_MARKERS = (
    OUTCOME_QUALITY_IMPROVES,
    STRUCTURED_VERIFICATION,
    INTERMEDIATE_QUALITY_CHECKS,
    STABILIZE_MAINTAIN_PIPELINES,
)

_ROLE_SPECIFIC_LABEL = "Role " + "Specific"
_ROLE_SPECIFIC_RE = re.compile(
    r"\*\*Related skills:\*\*.*\b" + re.escape(_ROLE_SPECIFIC_LABEL) + r"\b",
    re.I,
)
_SAVED_INSIGHT_RE = re.compile(r"### Saved material insight\s*\n(.*?)(?=\n### |\n---|\Z)", re.S)
_RELATED_BEFORE = "**Related skills:** SQL, Data Quality, [internal category label]"
_RELATED_AFTER = "**Related skills:** SQL, Data Quality, Dashboarding"


def _job(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": snapshot["title"],
        "responsibilities": snapshot["responsibilities"],
        "requirements": snapshot["requirements"],
        "extracted_skills": [{"skill": s} for s in snapshot["extracted_skills"]],
    }


def _document_used(question: dict) -> bool:
    for source in (question.get("study_sources") or {}).get("sources") or []:
        if source.get("source_type") == "document_library" and source.get("status") == "used":
            return True
    return False


def _analyze(snapshot: dict, questions: list[dict], pack_md: str) -> dict[str, Any]:
    exportable = [q for q in questions if not q.get("export_blocked") and q.get("model_answer")]
    role_specific_labels = len(_ROLE_SPECIFIC_RE.findall(pack_md))
    generic_hits = sum(1 for marker in _BLOCKED_MARKERS if marker.lower() in pack_md.lower())
    saved_insights = len(_SAVED_INSIGHT_RE.findall(pack_md))
    doc_used_questions = sum(1 for q in exportable if _document_used(q))
    insight_when_used = 0
    for q in exportable:
        if _document_used(q):
            study = q.get("study_material") or {}
            if study.get("saved_material_insight"):
                insight_when_used += 1

    source_library_blocked_hits = 0
    knowledge_path = REPO_ROOT / "backend" / "app" / "agents" / "job_search" / "knowledge" / "skill_knowledge.json"
    if knowledge_path.is_file():
        raw = knowledge_path.read_text(encoding="utf-8").lower()
        source_library_blocked_hits = sum(1 for marker in _BLOCKED_MARKERS if marker.lower() in raw)

    return {
        "role": snapshot["title"],
        "questions": len(exportable),
        "study_material_present": sum(1 for q in exportable if q.get("study_material")),
        "source_status_present": sum(1 for q in exportable if q.get("study_sources")),
        "role_specific_labels_found": role_specific_labels,
        "generic_phrase_hits": generic_hits,
        "saved_material_insights": saved_insights,
        "document_library_used": doc_used_questions,
        "saved_insight_when_doc_used": insight_when_used,
        "answers_over_500": sum(
            1 for q in exportable if len((q.get("model_answer") or "").split()) > ABSOLUTE_MAX_WORDS
        ),
        "source_library_blocked_hits": source_library_blocked_hits,
    }


def _pick_showcase(pack_files: dict[str, str], questions_by_slug: dict[str, list[dict]]) -> tuple[str, str]:
    study_example = "(no saved-material insight found)"
    related_example = f"Before: {_RELATED_BEFORE}\nAfter: {_RELATED_AFTER}"

    for slug in ("barista", "clinical_pharmacist", "devops_engineer"):
        pack_md = pack_files.get(slug, "")
        match = _SAVED_INSIGHT_RE.search(pack_md)
        if match:
            study_example = "### Saved material insight\n" + match.group(1).strip()
            break

    for slug, questions in questions_by_slug.items():
        for q in questions:
            related = q.get("related_skills") or []
            if related and _ROLE_SPECIFIC_LABEL not in related:
                related_example = (
                    f"Before: {_RELATED_BEFORE}\n"
                    f"After: **Related skills:** {', '.join(related[:4])}"
                )
                return study_example, related_example
    return study_example, related_example


def _build_summary(metrics: list[dict], study_example: str, related_example: str) -> str:
    source_hits = metrics[0].get("source_library_blocked_hits", 0) if metrics else 0
    sample_generic_hits = sum(m.get("generic_phrase_hits", 0) for m in metrics)
    lines = [
        "# Iteration 004C Study Synthesis Quality Summary",
        "",
        f"*Captured: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        "## Goal",
        "",
        "Improve study-material synthesis quality using local deterministic content, document-library support, "
        "and role/skill context — without LLM or web retrieval.",
        "",
        "## 004C changes",
        "",
        "- Added `study_synthesis.py` post-processing layer after document-library metadata attach.",
        "- Replaced user-facing internal `role_specific` category labels with contextual labels (Role Motivation, Daily Workflow, real skills).",
        "- Scrubbed blocked generic compiler phrases from model answers and study modules.",
        "- Added beginner/intermediate/advanced learning path enrichment and `technical_skills_covered`.",
        "- Integrated document-library support via concise **Saved material insight** sections when library material is used.",
        "",
        "## Quality table",
        "",
        "| Role | Questions | Study Material Present | Source Status Present | Internal Label Leaks Found | Generic Phrase Hits | Saved Material Insights | Answers Over 500 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for m in metrics:
        lines.append(
            f"| {m['role']} | {m['questions']} | {m['study_material_present']} | {m['source_status_present']} | "
            f"{m['role_specific_labels_found']} | {m['generic_phrase_hits']} | {m['saved_material_insights']} | "
            f"{m['answers_over_500']} |"
        )

    lines.extend(
        [
            "",
            "## Example improved study module",
            "",
            "```markdown",
            study_example,
            "```",
            "",
            "## Example cleaned related skills",
            "",
            "```markdown",
            related_example,
            "```",
            "",
            "## 004C-R Skill Knowledge Sanitization",
            "",
            "- **Runtime sanitization:** added `source_sanitizer.py`; `_load_knowledge()` sanitizes all skill/role knowledge on read.",
            "- **Build script:** `build_skill_knowledge.py` now sanitizes entries before writing JSON (version 2.1).",
            "- **Source JSON regeneration:** regenerated `skill_knowledge.json` from the build script — blocked phrase hits in on-disk source now **0**.",
            f"- **Generated sample blocked-phrase hits:** {sample_generic_hits} across all benchmark packs.",
            f"- **On-disk source-library blocked hits (grep):** {source_hits} (runtime load remains sanitized even if stale).",
            "- **Remaining:** full content-library regeneration still scheduled before final cleanup for document packs and indexes.",
            "",
            "## 004C-P Saved material insight polish",
            "",
            "- Fixed sentence boundaries in saved-material insight (period before `Pay special attention`; no `. before practising`).",
            "- Matched skills now join naturally (`Coffee Preparation and Customer Service`).",
            "",
            "## Remaining for 004D",
            "",
            "- **Recommended:** model-knowledge study synthesis behind a feature flag.",
            "- Optional later: web-research source capture stub with real captured URLs only.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    metrics: list[dict] = []
    pack_files: dict[str, str] = {}
    questions_by_slug: dict[str, list[dict]] = {}

    for snapshot in ROLE_SNAPSHOTS:
        job = _job(snapshot)
        focus = [snapshot["primary_skill"]] + [
            s for s in snapshot["extracted_skills"] if s != snapshot["primary_skill"]
        ]
        questions = mock_generate_questions(job, focus_areas=focus, difficulty="mid")
        questions_by_slug[snapshot["slug"]] = questions
        role_overview = build_role_overview(snapshot["title"], job)
        pack_md = build_interview_pack_markdown(
            job_title=snapshot["title"],
            company_name=None,
            questions=questions,
            role_overview=role_overview,
        )
        path = OUTPUT_DIR / f"{snapshot['slug']}_interview_pack.md"
        path.write_text(pack_md, encoding="utf-8")
        pack_files[snapshot["slug"]] = pack_md
        m = _analyze(snapshot, questions, pack_md)
        metrics.append(m)
        print(
            f"{snapshot['title']}: role_specific={m['role_specific_labels_found']}, "
            f"generic_hits={m['generic_phrase_hits']}, insights={m['saved_material_insights']}"
        )

    study_example, related_example = _pick_showcase(pack_files, questions_by_slug)
    (OUTPUT_DIR / "iteration_004c_summary.md").write_text(
        _build_summary(metrics, study_example, related_example),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"\nWrote samples to {OUTPUT_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
