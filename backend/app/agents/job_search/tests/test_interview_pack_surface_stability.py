"""Surface stability tests — Iteration 003A interview-pack stabilization."""

from __future__ import annotations

import json

import pytest

from app.agents.job_search.knowledge.coverage_planner import _hr_motivation_question
from app.agents.job_search.mock_data import finalize_questions_list, mock_generate_questions
from app.agents.job_search.quality.answer_length_policy import ABSOLUTE_MAX_WORDS
from app.agents.job_search.quality.surface_text_normalize import (
    find_joined_word_artifacts,
    has_unresolved_placeholders,
)

ROLE_SNAPSHOTS = [
    {
        "title": "Data Analyst",
        "primary_skill": "SQL",
        "responsibilities": [
            "SQL querying and dashboard creation for stakeholder reporting",
            "Data cleaning, data quality checks, and KPI/metrics reporting",
        ],
        "requirements": ["SQL querying", "dashboard creation", "Excel or BI tools", "data quality checks"],
        "extracted_skills": ["SQL", "Data Quality", "Dashboarding", "Excel"],
    },
    {
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


def _job(snapshot: dict) -> dict:
    return {
        "title": snapshot["title"],
        "responsibilities": snapshot["responsibilities"],
        "requirements": snapshot["requirements"],
        "extracted_skills": [{"skill": s} for s in snapshot["extracted_skills"]],
    }


def _generate(snapshot: dict) -> list[dict]:
    job = _job(snapshot)
    focus = [snapshot["primary_skill"]] + [
        s for s in snapshot["extracted_skills"] if s != snapshot["primary_skill"]
    ]
    return mock_generate_questions(job, focus_areas=focus, difficulty="mid")


def _exportable(questions: list[dict]) -> list[dict]:
    return [q for q in questions if not q.get("export_blocked") and q.get("model_answer")]


def _blob(questions: list[dict]) -> str:
    parts: list[str] = []
    for q in questions:
        parts.append(q.get("question") or "")
        parts.append(q.get("model_answer") or "")
        parts.append(json.dumps(q.get("study_material") or {}))
    return "\n".join(parts)


@pytest.mark.parametrize("snapshot", ROLE_SNAPSHOTS, ids=[s["title"] for s in ROLE_SNAPSHOTS])
def test_no_joined_word_artifacts(snapshot: dict) -> None:
    questions = _exportable(_generate(snapshot))
    hits = find_joined_word_artifacts(_blob(questions))
    assert not hits, f"{snapshot['title']} joined-word artifacts: {hits}"


@pytest.mark.parametrize("snapshot", ROLE_SNAPSHOTS, ids=[s["title"] for s in ROLE_SNAPSHOTS])
def test_no_bracket_placeholders(snapshot: dict) -> None:
    questions = _exportable(_generate(snapshot))
    for q in questions:
        for field in ("question", "model_answer", "answer_explanation"):
            text = q.get(field) or ""
            assert not has_unresolved_placeholders(text), (
                f"{snapshot['title']} / {q.get('question_id')} has bracket placeholder in {field}: {text[:120]}"
            )
        study_blob = json.dumps(q.get("study_material") or {})
        assert not has_unresolved_placeholders(study_blob), (
            f"{snapshot['title']} / {q.get('question_id')} study material has bracket placeholder"
        )


def test_hr_questions_are_role_specific() -> None:
    hr_questions = [_hr_motivation_question(_job(s)) for s in ROLE_SNAPSHOTS]
    assert len(set(hr_questions)) == len(hr_questions), "HR motivation questions must not be identical across roles"
    for snapshot, question in zip(ROLE_SNAPSHOTS, hr_questions, strict=True):
        role_l = snapshot["title"].lower()
        assert role_l in question.lower()
        assert "strong fit for our team" not in question.lower()


def test_hr_questions_contain_role_keywords() -> None:
    expectations: dict[str, list[str]] = {
        "Data Analyst": ["sql", "dashboard", "kpi", "stakeholder", "data quality"],
        "Electrical Engineer": [
            "load calculation",
            "cable sizing",
            "commissioning",
            "site coordination",
            "compliant",
        ],
        "Clinical Pharmacist": [
            "medication review",
            "prescribing safety",
            "counselling",
            "governance",
        ],
        "Barista": [
            "drink quality",
            "hygiene",
            "allergen",
            "customer service",
            "rush",
        ],
        "DevOps Engineer": [
            "deployment",
            "monitoring",
            "incident response",
            "automation",
            "aws",
        ],
    }
    for snapshot in ROLE_SNAPSHOTS:
        question = _hr_motivation_question(_job(snapshot)).lower()
        for keyword in expectations[snapshot["title"]]:
            assert keyword in question, f"{snapshot['title']} HR missing keyword: {keyword}"


def test_normalize_operationaldata_and_banned_joins() -> None:
    from app.agents.job_search.quality.surface_text_normalize import normalize_surface_text

    samples = {
        "messy operationaldata into trusted SQL": "messy operational data into trusted SQL",
        "production systemsand tools": "production systems and tools",
        "consistent milksteaming during rush": "consistent milk steaming during rush",
        "a strongfit for the team": "a strong fit for the team",
    }
    for raw, expected in samples.items():
        assert normalize_surface_text(raw) == expected
        assert not find_joined_word_artifacts(normalize_surface_text(raw))


def test_truncate_at_word_never_cuts_mid_word() -> None:
    from app.agents.job_search.quality.surface_text_normalize import truncate_at_word

    text = (
        "Why are you pursuing this Electrical Engineer role, and how would you deliver safe, "
        "compliant electrical work across load calculations, cable sizing, commissioning, "
        "and site coordination?"
    )
    preview = truncate_at_word(text, 180)
    assert preview.endswith("…")
    assert "coordi" not in preview
    assert "coordination" in preview or "commissioning" in preview


def test_clinical_pharmacist_no_ghs_clp_contamination() -> None:
    snapshot = next(s for s in ROLE_SNAPSHOTS if s["title"] == "Clinical Pharmacist")
    questions = _exportable(_generate(snapshot))
    blob = _blob(questions).lower()
    assert "ghs/clp" not in blob, "Clinical Pharmacist pack should not contain GHS/CLP contamination"
    assert "reach/coshh" not in blob


def test_live_path_finalize_applies_coverage() -> None:
    snapshot = ROLE_SNAPSHOTS[0]
    job = _job(snapshot)
    seed = [
        {
            "category": "technical",
            "question": "Explain a SQL reporting approach for stakeholder dashboards.",
            "why_asked": "Technical depth",
            "skill_tag": "SQL",
            "question_type": "explain",
        }
    ]
    finalized = finalize_questions_list(seed, job, "mid")
    categories = {q.get("category") for q in finalized}
    assert "hr" in categories
    assert "daily_routine" in categories
    assert all(q.get("study_material") for q in finalized)
    assert all(len((q.get("model_answer") or "").split()) <= ABSOLUTE_MAX_WORDS for q in finalized)


@pytest.mark.parametrize("snapshot", ROLE_SNAPSHOTS, ids=[s["title"] for s in ROLE_SNAPSHOTS])
def test_answers_under_500_words(snapshot: dict) -> None:
    questions = _exportable(_generate(snapshot))
    for q in questions:
        words = len((q.get("model_answer") or "").split())
        assert words <= ABSOLUTE_MAX_WORDS, (
            f"{snapshot['title']} answer over limit ({words} words) for {q.get('question_id')}"
        )
