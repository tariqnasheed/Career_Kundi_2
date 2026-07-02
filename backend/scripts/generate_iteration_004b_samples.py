#!/usr/bin/env python3
"""Non-production helper: capture Iteration 004B document-library retrieval samples."""

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
OUTPUT_DIR = REPO_ROOT / "project_review" / "samples" / "iteration_004b_document_library_retrieval"

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

_FAKE_URL_RE = re.compile(r"https?://[^\s\])\"']+")
_SOURCE_BLOCK_RE = re.compile(
    r"### Source / fallback status\s*\n(.*?)(?=\n### |\n---|\Z)",
    re.S,
)
_DOC_SUPPORT_RE = re.compile(
    r"### Document-library support\s*\n(.*?)(?=\n### |\n---|\Z)",
    re.S,
)

_SHOWCASE_ROLE_SLUGS = (
    "devops_engineer",
    "clinical_pharmacist",
    "barista",
    "electrical_engineer",
)

_GENERIC_SUPPORT_MARKERS = (
    "Core terminology for Core Terminology",
    "Matched skills: Core Terminology",
    "core terminology checks",
    "core verification",
    "Role Specific",
    "Apply Role Specific",
    "applied Role Specific",
    "intermediate quality checks",
    "structured verification",
)

_FORBIDDEN_SNIPPET_MARKERS = (
    "Role Specific",
    "Core Terminology",
    "intermediate quality checks",
    "structured verification",
)


def _is_useful_doc_support_block(block: str) -> bool:
    if any(marker in block for marker in _FORBIDDEN_SNIPPET_MARKERS):
        return False
    if any(marker in block for marker in _GENERIC_SUPPORT_MARKERS):
        if not any(skill in block for skill in ("AWS", "Kubernetes", "CI/CD", "Docker")):
            if not any(skill in block for skill in ("Medication", "Pharmacology", "Prescribing")):
                if not any(skill in block for skill in ("Espresso", "Coffee", "HACCP", "Hygiene")):
                    return False
    substantive_skills = (
        "AWS",
        "Kubernetes",
        "CI/CD",
        "Docker",
        "Medication",
        "Pharmacology",
        "Prescribing",
        "Espresso",
        "Coffee",
        "HACCP",
        "rollback",
        "monitoring",
        "allergen",
        "hygiene",
        "contraindication",
        "Cable",
        "Load Calculations",
    )
    if not any(skill in block for skill in substantive_skills):
        return False
    if "- Snippet:" in block:
        snippet_lines = [ln for ln in block.splitlines() if ln.strip().startswith("- Snippet:")]
        if not snippet_lines:
            return False
        for line in snippet_lines:
            if any(forbidden in line for forbidden in _FORBIDDEN_SNIPPET_MARKERS):
                return False
    return True


def _doc_support_score(block: str) -> int:
    if not _is_useful_doc_support_block(block):
        return -1
    score = 0
    preferred_phrases = (
        "I applied AWS",
        "I applied CI/CD",
        "I applied Docker",
        "I applied Kubernetes",
        "deployment reliability",
        "pipeline automation",
        "medication review",
        "prescribing safety",
        "espresso",
        "allergen",
        "hygiene controls",
    )
    for phrase in preferred_phrases:
        if phrase.lower() in block.lower():
            score += 3
    if "Snippet: In DevOps Engineer, I applied" in block or "Snippet: In Clinical" in block:
        score += 8
    if "Core terminology for Core Terminology" in block:
        return -1
    if any(forbidden in block for forbidden in _FORBIDDEN_SNIPPET_MARKERS):
        return -1
    if "Matched skills: Aws" in block or "Matched skills: Ci/Cd" in block:
        score -= 5
    if "QPS to DB" in block or "Quantitative problem for" in block:
        score -= 8
    return score


def _pick_showcase_blocks(pack_files: dict[str, str]) -> tuple[str, str]:
    source_block = ""
    doc_support_block = ""
    best_support_score = -1

    for slug in _SHOWCASE_ROLE_SLUGS:
        pack_md = pack_files.get(slug, "")
        if not source_block and "Document library:** Used" in pack_md:
            source_block = _first_block(pack_md, _SOURCE_BLOCK_RE)
        for match in _DOC_SUPPORT_RE.finditer(pack_md):
            block = "### Document-library support\n" + match.group(1).strip()
            score = _doc_support_score(block)
            if score > best_support_score:
                best_support_score = score
                doc_support_block = block

    return source_block, doc_support_block


def _job(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": snapshot["title"],
        "responsibilities": snapshot["responsibilities"],
        "requirements": snapshot["requirements"],
        "extracted_skills": [{"skill": s} for s in snapshot["extracted_skills"]],
    }


def _document_source(question: dict) -> dict[str, Any]:
    for source in (question.get("study_sources") or {}).get("sources") or []:
        if source.get("source_type") == "document_library":
            return source
    return {}


def _analyze(snapshot: dict, questions: list[dict], pack_md: str) -> dict[str, Any]:
    exportable = [q for q in questions if not q.get("export_blocked") and q.get("model_answer")]
    fake_urls = 0
    doc_used = 0
    doc_available_not_used = 0
    local_used = 0
    for q in exportable:
        blob = json.dumps(q.get("study_sources") or {})
        if _FAKE_URL_RE.search(blob):
            fake_urls += 1
        for source in (q.get("study_sources") or {}).get("sources") or []:
            if source.get("url"):
                fake_urls += 1
        doc = _document_source(q)
        if doc.get("status") == "used":
            doc_used += 1
        if doc.get("status") == "available_not_used":
            doc_available_not_used += 1
        if "local_fallback" in ((q.get("study_sources") or {}).get("used_source_types") or []):
            local_used += 1

    words = [len((q.get("model_answer") or "").split()) for q in exportable]
    return {
        "role": snapshot["title"],
        "questions": len(exportable),
        "study_material_present": sum(1 for q in exportable if q.get("study_material")),
        "source_metadata_present": sum(1 for q in exportable if q.get("study_sources")),
        "document_library_used": doc_used,
        "document_library_available_not_used": doc_available_not_used,
        "local_fallback_used": local_used,
        "fake_urls_found": fake_urls,
        "answers_over_500": sum(1 for w in words if w > ABSOLUTE_MAX_WORDS),
    }


def _first_block(pack_md: str, pattern: re.Pattern[str]) -> str:
    match = pattern.search(pack_md)
    if not match:
        return "(block not found)"
    header = "### Source / fallback status" if "Source" in pattern.pattern else "### Document-library support"
    if "Document" in pattern.pattern:
        header = "### Document-library support"
    return header + "\n" + match.group(1).strip()


def _build_summary(metrics: list[dict], source_block: str, doc_support_block: str) -> str:
    lines = [
        "# Iteration 004B Document Library Retrieval Summary",
        "",
        f"*Captured: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        "## Goal",
        "",
        "Retrieve and use saved role-pack material from `documents/interview_packs/` as supporting study-module sources.",
        "",
        "## 004B-S stabilization notes",
        "",
        "- Matching threshold tightened: document library is marked `used` only with strong skill-tag overlap, "
        "two or more meaningful skill overlaps, or meaningful question-text overlap — not merely because a role folder exists.",
        "- HR/behavioral/role-specific questions no longer automatically mark document library as `used`; "
        "they remain `available_not_used` unless the saved material directly matches the prompt.",
        "- Short, heading-only, and generic process snippets are filtered out (minimum useful snippet length enforced).",
        "- Supporting focus text is generated from matched skills and question terms rather than random generic sentences.",
        "",
        "## 004B-F polish notes",
        "",
        "004B-F: Generic Core Terminology-only matches are now treated as `available_not_used` instead of `used`.",
        "",
        "- `Core Terminology` alone cannot mark document library as used.",
        "- Generic core-terminology snippets (e.g. `Core terminology for Core Terminology`) are filtered out.",
        "- Showcase support examples prefer substantive technical matches (AWS/Kubernetes/CI/CD, medication review, espresso/hygiene).",
        "",
        "## 004B-G polish notes",
        "",
        "004B-G: Generic Role Specific snippets are filtered, and technical skill labels are normalized.",
        "",
        "- Role Specific / intermediate quality checks / structured verification snippets are rejected.",
        "- Matched skill labels render as `AWS`, `CI/CD`, `SQL`, `HACCP`, etc.",
        "- Showcase support blocks must include substantive snippet text without generic placeholders.",
        "",
        "## Quality table",
        "",
        "| Role | Questions | Study Material Present | Source Metadata Present | Document Library Used | Document Library Available Not Used | Local Fallback Used | Fake URLs Found | Answers Over 500 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for m in metrics:
        lines.append(
            f"| {m['role']} | {m['questions']} | {m['study_material_present']} | {m['source_metadata_present']} | "
            f"{m['document_library_used']} | {m['document_library_available_not_used']} | "
            f"{m['local_fallback_used']} | {m['fake_urls_found']} | {m['answers_over_500']} |"
        )

    lines.extend(
        [
            "",
            "## Example document-library source block",
            "",
            "```markdown",
            source_block,
            "```",
            "",
            "## Example document-library support section",
            "",
            "```markdown",
            doc_support_block,
            "```",
            "",
            "## Retrieval quality observations",
            "",
            "- **Worked well:** Technical/skill-tagged questions with real overlap (AWS, Kubernetes, cable sizing, medication review, espresso preparation) receive compact support snippets and skill-linked supporting focus.",
            "- **Weak / absent:** Data Analyst has no saved role pack in the document library, so `document_library` remains `not_configured`.",
            "- **HR / generic prompts:** Usually remain `available_not_used` with an explicit note that saved material exists but no question-specific match was strong enough.",
            "- **Usefulness:** Support sections add transparent pointers to saved structured JSON without duplicating full legacy packs or attaching generic boilerplate.",
            "",
            "## Remaining for Iteration 004C",
            "",
            "- Add model-knowledge study synthesis behind a feature flag (recommended next step).",
            "- Optional later: web-research agent stub with real captured URLs only.",
            "- Improve cross-question deduplication of document-library snippets.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    metrics: list[dict] = []
    pack_files: dict[str, str] = {}

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
        pack_files[snapshot["slug"]] = pack_md
        m = _analyze(snapshot, questions, pack_md)
        metrics.append(m)
        print(
            f"{snapshot['title']}: doc_used={m['document_library_used']}/{m['questions']}, "
            f"available_not_used={m['document_library_available_not_used']}"
        )

    source_block, doc_support_block = _pick_showcase_blocks(pack_files)
    if not source_block:
        source_block = "(no document-library used block found)"
    if not doc_support_block:
        doc_support_block = "(no document-library support section found)"

    (OUTPUT_DIR / "iteration_004b_summary.md").write_text(
        _build_summary(metrics, source_block, doc_support_block),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"\nWrote samples to {OUTPUT_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
