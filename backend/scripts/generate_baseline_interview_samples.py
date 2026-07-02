#!/usr/bin/env python3
"""Non-production helper: capture Iteration 002 baseline interview-pack Markdown samples."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Allow `uv run python backend/scripts/generate_baseline_interview_samples.py` from repo root.
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.answer_length_policy import ABSOLUTE_MAX_WORDS
from app.agents.job_search.quality.generic_phrase_audit import generic_phrase_count
from app.agents.job_search.quality.study_material_phrase_audit import study_banned_phrase_count
from app.services.role_pack_library import build_role_overview
from app.tools.document_export import build_interview_pack_markdown, build_study_material_markdown

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "project_review" / "samples" / "iteration_002_baseline"

STUDY_SECTION_MARKERS = (
    "**Core idea:**",
    "**How to apply it:**",
    "**Common mistakes:**",
    "**Interview tip:**",
    "**Standards / safety / compliance note:**",
)

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
            "SQL querying",
            "dashboard creation",
            "stakeholder reporting",
            "data cleaning",
            "data quality checks",
            "query performance",
            "KPI/metrics reporting",
            "Excel or BI tools",
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
            "LV distribution",
            "load calculations",
            "cable sizing",
            "lighting or power layout review",
            "testing and commissioning",
            "electrical safety",
            "standards/compliance",
            "site coordination",
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
            "medication review",
            "prescribing safety",
            "patient counselling",
            "clinical documentation",
            "escalation",
            "governance",
            "multidisciplinary working",
            "risk management",
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
            "espresso preparation",
            "milk steaming",
            "drink consistency",
            "hygiene",
            "allergens",
            "customer service",
            "speed during rush hours",
            "stock handling",
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
            "AWS",
            "CI/CD",
            "Docker",
            "Kubernetes",
            "monitoring",
            "incident response",
            "security",
            "rollback/recovery",
            "infrastructure automation",
        ],
        "extracted_skills": ["AWS", "CI/CD", "Docker", "Kubernetes", "Monitoring"],
    },
]


def _job_from_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    skills = snapshot["extracted_skills"]
    return {
        "title": snapshot["title"],
        "responsibilities": snapshot["responsibilities"],
        "requirements": snapshot["requirements"],
        "extracted_skills": [{"skill": skill} for skill in skills],
    }


def _visible_study_sections(pack_markdown: str) -> int:
    count = 0
    for block in re.split(r"^### Study material\s*$", pack_markdown, flags=re.M)[1:]:
        section = block.split("### Model answer", 1)[0]
        if sum(1 for marker in STUDY_SECTION_MARKERS if marker in section) >= 2:
            count += 1
    return count


def _missing_coverage_notes(categories: set[str], question_types: set[str], qtext_blob: str) -> str:
    missing: list[str] = []
    checks = {
        "HR questions": any("hr" in c for c in categories) or "human resources" in qtext_blob,
        "behavioral questions": "behavioral" in categories,
        "technical questions": "technical" in categories,
        "conceptual questions": any(t in question_types for t in ("explain", "principles", "terminology")),
        "scenario questions": any(t in question_types for t in ("scenario", "complex_problem")),
        "daily routine questions": any(k in qtext_blob for k in ("day-one", "daily", "typical task", "routine")),
        "responsibility-specific questions": "deliver " in qtext_blob or "responsibilit" in qtext_blob,
        "skill-specific questions": True,
        "tool/software questions": any(k in qtext_blob for k in ("tool", "software", "aws", "docker", "sql", "excel")),
        "standards/safety questions": any(
            k in qtext_blob for k in ("standard", "safety", "compliance", "haccp", "bs 7671", "governance")
        ),
        "seniority variations": any(k in qtext_blob for k in ("junior", "senior", "lead", "apprentice", "newly qualified")),
        "company-specific questions": "company_specific" in categories,
    }
    for label, present in checks.items():
        if not present:
            missing.append(label)
    return "; ".join(missing) if missing else "none noted in this snapshot"


def _analyze_role(snapshot: dict[str, Any], questions: list[dict[str, Any]], pack_md: str) -> dict[str, Any]:
    exportable = [q for q in questions if not q.get("export_blocked")]
    answers = [(q.get("model_answer") or "").strip() for q in exportable]
    answers = [a for a in answers if a]
    word_counts = [len(a.split()) for a in answers]
    categories = sorted({str(q.get("category") or "unknown") for q in exportable})
    question_types = sorted({str(q.get("question_type") or "") for q in exportable if q.get("question_type")})
    skills = sorted(
        {
            str(q.get("mapped_skill") or q.get("skill_tag"))
            for q in exportable
            if q.get("mapped_skill") or q.get("skill_tag")
        }
    )
    study_present = all(bool(q.get("study_material")) for q in exportable if answers)
    generic_in_answers = sum(generic_phrase_count(a) for a in answers)
    study_blob = " ".join(
        json.dumps(q.get("study_material") or {})
        for q in exportable
    )
    generic_in_study = study_banned_phrase_count(study_blob)
    qtext_blob = " ".join((q.get("question") or "").lower() for q in exportable)

    short_behavioral = 0
    for q in exportable:
        if str(q.get("category") or "").lower() == "behavioral":
            words = len((q.get("model_answer") or "").split())
            if words and words < 80:
                short_behavioral += 1

    return {
        "role": snapshot["title"],
        "questions_generated": len(exportable),
        "categories_covered": ", ".join(categories),
        "skills_covered": ", ".join(skills) if skills else "none tagged",
        "study_material_all": "yes" if study_present else "no",
        "avg_answer_words": round(sum(word_counts) / len(word_counts), 1) if word_counts else 0,
        "max_answer_words": max(word_counts) if word_counts else 0,
        "answers_over_500": sum(1 for w in word_counts if w > ABSOLUTE_MAX_WORDS),
        "study_visible_sections": _visible_study_sections(pack_md),
        "generic_phrases": generic_in_answers + generic_in_study,
        "missing_coverage": _missing_coverage_notes(set(categories), set(question_types), qtext_blob),
        "short_behavioral_count": short_behavioral,
        "blocked_count": len(questions) - len(exportable),
    }


def _build_summary(metrics: list[dict[str, Any]], files: list[str]) -> str:
    lines = [
        "# Iteration 002 Baseline Summary",
        "",
        f"*Captured: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        "## Generation method",
        "",
        "- Script: `backend/scripts/generate_baseline_interview_samples.py`",
        "- Functions: `mock_generate_questions`, `build_role_overview`, `build_interview_pack_markdown`, `build_study_material_markdown`",
        "- Production logic changed: **no** (capture-only helper script and review docs)",
        "",
        "## Sample files generated",
        "",
    ]
    for path in files:
        lines.append(f"- `{path}`")
    lines.extend(["", "## Metrics table", ""])
    header = (
        "| Role | Questions generated | Categories covered | Skills covered | Study material present for every question | "
        "Average answer word count | Max answer word count | Answers over 500 words | Study modules with visible sections | "
        "Generic phrases noticed | Missing coverage noticed |"
    )
    sep = "|" + "|".join(["---"] * 11) + "|"
    lines.extend([header, sep])
    for m in metrics:
        lines.append(
            f"| {m['role']} | {m['questions_generated']} | {m['categories_covered']} | {m['skills_covered']} | "
            f"{m['study_material_all']} | {m['avg_answer_words']} | {m['max_answer_words']} | {m['answers_over_500']} | "
            f"{m['study_visible_sections']} | {m['generic_phrases']} | {m['missing_coverage']} |"
        )

    lines.extend(
        [
            "",
            "## Job Search / Interview Pack observations",
            "",
            "Honest read of the five captured packs:",
            "",
            "- **Present today:** behavioral prompts tied to responsibilities; technical/skill-tagged compiler questions; some scenario/calculation/terminology variants; role-specific motivation prompt; standards/safety language in technical answers for engineering/healthcare/hospitality.",
            "- **Weak or missing today:** explicit HR category questions; dedicated daily-routine/day-one prompts; case-study category; seniority-tier question sets (junior vs senior); company-specific questions without company data; breadth across every listed requirement skill (focus skill drives most technical depth).",
            "- **Answer shape:** technical answers are substantially richer than behavioral STAR answers, which are often short template paragraphs.",
            "- **Export structure:** role overview, employer expectations, skill map, per-question study block, model answer, and follow-ups are present in Markdown exports.",
            "",
            "## Study Material observations",
            "",
            "- **Question-specific modules exist** for every exportable question in all five snapshots.",
            "- **Structured sections** (`Core idea`, `How to apply it`, `Common mistakes`, `Interview tip`) appear in exported Markdown for compiler-backed technical questions.",
            "- **Behavioral / motivation modules** reuse STAR-prep framing; they are question-linked but less technically deep.",
            "- **No source ladder metadata** (web/model/library/fallback) is exposed in study modules.",
            "- **Beginner/intermediate/advanced depth** is present in compiler study objects but export rendering compresses some modules visually.",
            "- **Not yet real multi-source learning material** — deterministic compiler/fallback content only.",
            "",
            "## Biggest baseline weaknesses",
            "",
        ]
    )

    weaknesses = [
        "No explicit HR question category in generated packs.",
        "Limited seniority variation (few dedicated junior/senior prompts per pack).",
        "Behavioral answers are often short (~40–80 words) compared with technical compiler answers.",
        "Requirement skills beyond the primary focus skill get uneven technical question coverage.",
        "No company-specific block unless company data is supplied.",
        "Study material lacks cited sources and fallback-status transparency.",
        "Daily routine / day-one operational questions are sparse or absent.",
        "Case-study category not consistently represented.",
    ]
    for item in weaknesses:
        lines.append(f"- {item}")

    short_roles = [m for m in metrics if m["short_behavioral_count"] > 0]
    if short_roles:
        lines.append(
            f"- Short behavioral answers observed in: {', '.join(m['role'] for m in short_roles)}."
        )

    lines.extend(
        [
            "",
            "## Next recommended implementation step",
            "",
            "Proceed to **Implementation order step 3 — Job Search + Interview Pack Generator fixes**: decouple popular-role auto-export on the frontend, improve job-import field coverage, and expand question generation templates for HR/daily-routine/seniority variants before further study-material architecture work.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generated_files: list[str] = []
    metrics: list[dict[str, Any]] = []

    for snapshot in ROLE_SNAPSHOTS:
        job = _job_from_snapshot(snapshot)
        focus = [snapshot["primary_skill"]] + [
            s for s in snapshot["extracted_skills"] if s != snapshot["primary_skill"]
        ]
        questions = mock_generate_questions(job, focus_areas=focus, difficulty="medium")
        role_overview = build_role_overview(snapshot["title"], job)

        pack_md = build_interview_pack_markdown(
            job_title=snapshot["title"],
            company_name=None,
            questions=questions,
            role_overview=role_overview,
        )
        pack_path = OUTPUT_DIR / f"{snapshot['slug']}_interview_pack.md"
        pack_path.write_text(pack_md, encoding="utf-8")
        generated_files.append(str(pack_path.relative_to(REPO_ROOT)))

        study_md = build_study_material_markdown(
            job_title=snapshot["title"],
            questions=questions,
            role_overview=role_overview,
        )
        study_path = OUTPUT_DIR / f"{snapshot['slug']}_study_only.md"
        study_path.write_text(study_md, encoding="utf-8")
        generated_files.append(str(study_path.relative_to(REPO_ROOT)))

        metrics.append(_analyze_role(snapshot, questions, pack_md))
        print(
            f"{snapshot['title']}: {metrics[-1]['questions_generated']} questions, "
            f"avg {metrics[-1]['avg_answer_words']} words, "
            f"study sections {metrics[-1]['study_visible_sections']}"
        )

    summary_path = OUTPUT_DIR / "baseline_summary.md"
    summary_path.write_text(_build_summary(metrics, generated_files), encoding="utf-8")
    generated_files.append(str(summary_path.relative_to(REPO_ROOT)))

    meta_path = OUTPUT_DIR / "metrics.json"
    meta_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    generated_files.append(str(meta_path.relative_to(REPO_ROOT)))

    print(f"\nWrote {len(generated_files)} files to {OUTPUT_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
