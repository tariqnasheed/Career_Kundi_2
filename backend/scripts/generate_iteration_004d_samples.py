#!/usr/bin/env python3
"""Non-production helper: capture Iteration 004D model-knowledge feature-flag samples."""

from __future__ import annotations

import json
import os
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Default model knowledge off before settings load.
os.environ.setdefault("JOB_SEARCH_ENABLE_MODEL_KNOWLEDGE", "false")
os.environ.setdefault("JOB_SEARCH_MODEL_KNOWLEDGE_PROVIDER", "disabled")

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.agents.job_search.knowledge.model_knowledge import (
    DeterministicTestModelKnowledgeProvider,
    build_role_specific_model_insight,
)
from app.agents.job_search.knowledge.study_synthesis import infer_role_family
from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.answer_length_policy import ABSOLUTE_MAX_WORDS
from app.agents.job_search.quality.blocked_phrase_guard import (
    INTERMEDIATE_QUALITY_CHECKS,
    OUTCOME_QUALITY_IMPROVES,
    STABILIZE_MAINTAIN_PIPELINES,
    STRUCTURED_VERIFICATION,
)
from app.data.popular_roles_catalog import catalog_role_to_job_snapshot, get_all_catalog_roles
from app.agents.job_search.quality.surface_text_normalize import normalize_surface_text
from app.services.role_pack_library import build_role_overview
from app.tools.document_export import build_interview_pack_markdown

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "project_review" / "samples" / "iteration_004d_model_knowledge_flag"
ITERATION_SEED = 42

FIXED_BENCHMARK_ROLES: list[dict[str, Any]] = [
    {
        "slug": "data_analyst",
        "title": "Data Analyst",
        "primary_skill": "SQL",
        "responsibilities": [
            "SQL querying and dashboard creation for stakeholder reporting",
            "Data cleaning, data quality checks, and KPI/metrics reporting",
        ],
        "requirements": ["SQL querying", "dashboard creation", "data quality checks", "Excel or BI tools"],
        "extracted_skills": ["SQL", "Data Quality", "Dashboarding", "Excel"],
    },
    {
        "slug": "electrical_engineer",
        "title": "Electrical Engineer",
        "primary_skill": "Electrical Installation",
        "responsibilities": [
            "LV distribution design support and load calculations",
            "Testing, commissioning, electrical safety, and standards compliance",
        ],
        "requirements": ["load calculations", "cable sizing", "electrical safety", "standards/compliance"],
        "extracted_skills": ["Electrical Installation", "Load Calculations", "Cable Sizing", "Commissioning"],
    },
    {
        "slug": "clinical_pharmacist",
        "title": "Clinical Pharmacist",
        "primary_skill": "Pharmacology",
        "responsibilities": [
            "Medication review, prescribing safety, and patient counselling",
            "Clinical documentation, escalation, and governance",
        ],
        "requirements": ["medication review", "prescribing safety", "governance", "risk management"],
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
        "requirements": ["espresso preparation", "hygiene", "allergens", "customer service"],
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
        "requirements": ["AWS", "CI/CD", "Docker", "Kubernetes", "monitoring", "security"],
        "extracted_skills": ["AWS", "CI/CD", "Docker", "Kubernetes", "Monitoring"],
    },
]

_RANDOM_ROLE_POOLS: dict[str, list[str]] = {
    "healthcare or education": ["Primary School Teacher", "Nurse"],
    "legal, finance, or business": ["Solicitor", "Financial Analyst"],
    "engineering or technical": ["Civil Engineer", "Mechanical Engineer"],
    "creative, media, or communication": ["Journalist", "Graphic Designer"],
    "non-traditional/trending": ["YouTuber", "Social Media Creator", "Podcaster", "Influencer", "Esports Player"],
}

_FALLBACK_SNAPSHOTS: dict[str, dict[str, Any]] = {
    "Nurse": {
        "slug": "nurse",
        "title": "Nurse",
        "primary_skill": "Patient Care",
        "responsibilities": ["Patient assessment, medication administration, and care documentation"],
        "requirements": ["patient assessment", "medication administration", "clinical documentation"],
        "extracted_skills": ["Patient Care", "Medication Administration", "Clinical Documentation"],
    },
    "YouTuber": {
        "slug": "youtuber",
        "title": "YouTuber",
        "primary_skill": "Content Creation",
        "responsibilities": ["Video planning, filming, editing, and audience engagement"],
        "requirements": ["content planning", "video editing", "audience engagement", "brand partnerships"],
        "extracted_skills": ["Content Creation", "Video Editing", "Audience Growth", "Storytelling"],
    },
    "Social Media Creator": {
        "slug": "social_media_creator",
        "title": "Social Media Creator",
        "primary_skill": "Content Strategy",
        "responsibilities": [
            "Platform content planning, filming, editing, and publishing on a consistent schedule",
            "Community engagement, analytics review, and brand-safe sponsorship integration",
            "Thumbnail/title testing, rights clearance, and reputation monitoring",
        ],
        "requirements": [
            "content strategy", "video editing", "community management", "analytics review",
            "brand partnerships", "publishing cadence", "copyright clearance",
        ],
        "extracted_skills": ["Content Strategy", "Video Editing", "Community Management", "Analytics", "Copywriting"],
    },
    "Podcaster": {
        "slug": "podcaster",
        "title": "Podcaster",
        "primary_skill": "Audio Production",
        "responsibilities": ["Episode research, recording, editing, and guest coordination"],
        "requirements": ["audio editing", "research", "interviewing", "audience growth"],
        "extracted_skills": ["Audio Production", "Interviewing", "Research", "Storytelling"],
    },
}

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
_MODEL_INSIGHT_RE = re.compile(r"### Model knowledge insight\s*\n(.*?)(?=\n### |\n---|\Z)", re.S)
_SOURCE_BLOCK_RE = re.compile(r"### Source / fallback status\s*\n(.*?)(?=\n### |\n---|\Z)", re.S)


def select_random_validation_roles(*, seed: int = ITERATION_SEED) -> list[dict[str, str]]:
    rng = random.Random(seed)
    selected: list[dict[str, str]] = []
    for category, roles in _RANDOM_ROLE_POOLS.items():
        selected.append({"title": rng.choice(roles), "category": category})
    return selected


def _catalog_snapshot(title: str) -> dict[str, Any] | None:
    for role in get_all_catalog_roles():
        if role.get("title") == title:
            job = catalog_role_to_job_snapshot(role)
            slug = title.lower().replace(" ", "_").replace("/", "_")
            skills = [s.get("skill") if isinstance(s, dict) else s for s in job.get("extracted_skills") or []]
            return {
                "slug": slug,
                "title": title,
                "primary_skill": skills[0] if skills else title,
                "responsibilities": job.get("responsibilities") or [],
                "requirements": job.get("requirements") or [],
                "extracted_skills": skills or [title],
            }
    return _FALLBACK_SNAPSHOTS.get(title)


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


def _model_used(question: dict) -> bool:
    for source in (question.get("study_sources") or {}).get("sources") or []:
        if source.get("source_type") == "model" and source.get("status") == "used":
            return True
    return False


def _analyze_fixed(snapshot: dict, questions: list[dict], pack_md: str) -> dict[str, Any]:
    exportable = [q for q in questions if not q.get("export_blocked") and q.get("model_answer")]
    return {
        "role": snapshot["title"],
        "questions": len(exportable),
        "study_material_present": sum(1 for q in exportable if q.get("study_material")),
        "source_status_present": sum(1 for q in exportable if q.get("study_sources")),
        "model_knowledge_used": sum(1 for q in exportable if _model_used(q)),
        "document_library_used": sum(1 for q in exportable if _document_used(q)),
        "saved_material_insights": len(re.findall(r"### Saved material insight", pack_md)),
        "model_insights": len(_MODEL_INSIGHT_RE.findall(pack_md)),
        "generic_phrase_hits": sum(1 for marker in _BLOCKED_MARKERS if marker.lower() in pack_md.lower()),
        "role_specific_leaks": len(_ROLE_SPECIFIC_RE.findall(pack_md)),
        "answers_over_500": sum(
            1 for q in exportable if len((q.get("model_answer") or "").split()) > ABSOLUTE_MAX_WORDS
        ),
    }


def _analyze_random(snapshot: dict, category: str, questions: list[dict], pack_md: str) -> dict[str, Any]:
    exportable = [q for q in questions if not q.get("export_blocked") and q.get("model_answer")]
    notes: list[str] = []
    if not snapshot.get("responsibilities"):
        notes.append("Minimal fallback snapshot")
    return {
        "role": snapshot["title"],
        "category": category,
        "questions": len(exportable),
        "study_material_present": sum(1 for q in exportable if q.get("study_material")),
        "source_status_present": sum(1 for q in exportable if q.get("study_sources")),
        "model_knowledge_used": sum(1 for q in exportable if _model_used(q)),
        "generic_phrase_hits": sum(1 for marker in _BLOCKED_MARKERS if marker.lower() in pack_md.lower()),
        "role_specific_leaks": len(_ROLE_SPECIFIC_RE.findall(pack_md)),
        "answers_over_500": sum(
            1 for q in exportable if len((q.get("model_answer") or "").split()) > ABSOLUTE_MAX_WORDS
        ),
        "notes": "; ".join(notes) if notes else "",
    }


def _generate_pack(snapshot: dict[str, Any]) -> tuple[list[dict], str]:
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
    return questions, pack_md


def _build_summary(
    *,
    fixed_metrics: list[dict],
    random_metrics: list[dict],
    random_roles: list[dict[str, str]],
    disabled_source_example: str,
    enabled_insight_example: str,
) -> str:
    lines = [
        "# Iteration 004D Model Knowledge Feature Flag Summary",
        "",
        f"*Captured: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        "## Goal",
        "",
        "Add model-knowledge study synthesis behind a disabled-by-default feature flag with deterministic "
        "test provider support and random validation sampling — no live web research or fake citations.",
        "",
        "## 004D changes",
        "",
        "- Added `model_knowledge.py` provider abstraction with `ModelKnowledgeStatus` and `ModelKnowledgeResult`.",
        "- Added `JOB_SEARCH_ENABLE_MODEL_KNOWLEDGE` and `JOB_SEARCH_MODEL_KNOWLEDGE_PROVIDER` settings.",
        "- Integrated model insight into `study_synthesis.py` and Markdown export.",
        "- Source ladder now reports disabled, used, or failed-fallback model-knowledge status transparently.",
        "- Sample generation now includes 5 fixed benchmark roles + 5 deterministic random validation roles.",
        "",
        "## Fixed benchmark metrics",
        "",
        "| Role | Questions | Study Material Present | Source Status Present | Model Knowledge Used | Document Library Used | Saved Material Insights | Model Insights | Generic Phrase Hits | Internal Label Leaks | Answers Over 500 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for m in fixed_metrics:
        lines.append(
            f"| {m['role']} | {m['questions']} | {m['study_material_present']} | {m['source_status_present']} | "
            f"{m['model_knowledge_used']} | {m['document_library_used']} | {m['saved_material_insights']} | "
            f"{m['model_insights']} | {m['generic_phrase_hits']} | {m['role_specific_leaks']} | {m['answers_over_500']} |"
        )

    lines.extend(
        [
            "",
            "## Random validation metrics",
            "",
            "| Role | Category | Questions | Study Material Present | Source Status Present | Model Knowledge Used | Generic Phrase Hits | Internal Label Leaks | Answers Over 500 | Notes |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for m in random_metrics:
        lines.append(
            f"| {m['role']} | {m['category']} | {m['questions']} | {m['study_material_present']} | "
            f"{m['source_status_present']} | {m['model_knowledge_used']} | {m['generic_phrase_hits']} | "
            f"{m['role_specific_leaks']} | {m['answers_over_500']} | {m.get('notes', '')} |"
        )

    lines.extend(
        [
            "",
            "## Example model-disabled source block",
            "",
            "```markdown",
            disabled_source_example.strip(),
            "```",
            "",
            "## Example model-enabled test insight",
            "",
            "*Deterministic test provider output (not a live model call):*",
            "",
            "```markdown",
            "### Model knowledge insight",
            "",
            enabled_insight_example.strip(),
            "```",
            "",
            "## Random validation roles selected",
            "",
            f"*Seed: {ITERATION_SEED}*",
            "",
        ]
    )
    for item in random_roles:
        lines.append(f"- **{item['title']}** — {item['category']}")

    journalist_q = next((m["questions"] for m in random_metrics if m["role"] == "Journalist"), 0)
    creator_q = next((m["questions"] for m in random_metrics if m["role"] == "Social Media Creator"), 0)

    lines.extend(
        [
            "",
            "## 004D-S Random Validation Coverage Stabilization",
            "",
            "- Added creative/media, creator/trending, and sports archetype coverage packs in `coverage_planner.py`.",
            "- Added evidence packs and legacy answer paths so creative roles no longer over-block on contract compiler.",
            "- Enforced exportable coverage floor (`MIN_EXPORTABLE_PACK_QUESTIONS = 28`) with meaningful supplemental categories.",
            "- **Journalist:** 17 → "
            f"{journalist_q} questions.",
            "- **Social Media Creator:** 14 → "
            f"{creator_q} questions.",
            "- Categories added include ethics/copyright, audience/platform/analytics, production workflow, practical tasks, "
            "case studies, daily routine, HR/motivation, and seniority/growth.",
            "- Added `test_random_validation_coverage.py`.",
            "",
        ]
    )

    lines.extend(
        [
            "",
            "## 004D-P Final summary polish",
            "",
            "- Normalized model-insight example text (`explaining how` spacing guard in `surface_text_normalize.py`).",
            "- Aligned **Remaining for 004E** with Job Posting Intelligence and Interview Pack Source Ladder roadmap.",
            "",
        ]
    )

    lines.extend(
        [
            "",
            "## Remaining for 004E",
            "",
            "- **Recommended:** Job Posting Intelligence and Interview Pack Source Ladder.",
            "- Complete job-posting/user-input parsing and job posting link extraction.",
            "- Company profile and scope understanding; exhaustive coverage of responsibilities, skills, tools, duties, domain context, and user notes.",
            "- Easy-to-hard question progression; block silly/filler questions; coverage audit before export.",
            "- Interview pack source ladder: user fields → link extraction → web research (real URLs) → model knowledge (flagged) → document library → local fallback.",
            "- Real user packs are coverage-driven; benchmark samples keep the 5+5 comparison rule.",
            "- Final PDF/database regeneration before cleanup (see `05_cleanup_plan.md`).",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    fixed_dir = OUTPUT_DIR / "fixed"
    random_dir = OUTPUT_DIR / "random_validation"
    fixed_dir.mkdir(parents=True, exist_ok=True)
    random_dir.mkdir(parents=True, exist_ok=True)

    fixed_metrics: list[dict] = []
    random_metrics: list[dict] = []
    disabled_source_example = ""
    first_questions: list[dict] | None = None

    for snapshot in FIXED_BENCHMARK_ROLES:
        questions, pack_md = _generate_pack(snapshot)
        if first_questions is None:
            first_questions = questions
        path = fixed_dir / f"{snapshot['slug']}_interview_pack.md"
        path.write_text(pack_md, encoding="utf-8")
        m = _analyze_fixed(snapshot, questions, pack_md)
        fixed_metrics.append(m)
        print(f"Fixed {snapshot['title']}: model_used={m['model_knowledge_used']}, generic_hits={m['generic_phrase_hits']}")

        if not disabled_source_example:
            match = _SOURCE_BLOCK_RE.search(pack_md)
            if match:
                disabled_source_example = "### Source / fallback status\n" + match.group(1).strip()

    random_roles = select_random_validation_roles(seed=ITERATION_SEED)
    for item in random_roles:
        snapshot = _catalog_snapshot(item["title"])
        if not snapshot:
            print(f"Skipping missing snapshot for {item['title']}")
            continue
        questions, pack_md = _generate_pack(snapshot)
        path = random_dir / f"{snapshot['slug']}_interview_pack.md"
        path.write_text(pack_md, encoding="utf-8")
        m = _analyze_random(snapshot, item["category"], questions, pack_md)
        random_metrics.append(m)
        print(f"Random {snapshot['title']}: questions={m['questions']}, generic_hits={m['generic_phrase_hits']}")

    devops_job = _job(next(s for s in FIXED_BENCHMARK_ROLES if s["slug"] == "devops_engineer"))
    enabled_insight_example = normalize_surface_text(
        build_role_specific_model_insight(
            role="DevOps Engineer",
            role_family=infer_role_family(devops_job),
        )
    )
    provider_note = DeterministicTestModelKnowledgeProvider().provider_name

    summary = _build_summary(
        fixed_metrics=fixed_metrics,
        random_metrics=random_metrics,
        random_roles=random_roles,
        disabled_source_example=disabled_source_example,
        enabled_insight_example=enabled_insight_example,
    )
    summary += f"\n*Test provider name: `{provider_note}` — used only when feature flag + provider are explicitly enabled.*\n"

    (OUTPUT_DIR / "iteration_004d_summary.md").write_text(summary, encoding="utf-8")
    (OUTPUT_DIR / "metrics.json").write_text(
        json.dumps({"fixed": fixed_metrics, "random_validation": random_metrics, "seed": ITERATION_SEED}, indent=2),
        encoding="utf-8",
    )
    print(f"\nWrote samples to {OUTPUT_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
