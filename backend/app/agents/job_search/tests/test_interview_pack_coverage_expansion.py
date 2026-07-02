"""Coverage expansion tests — Iteration 003 interview-pack generator."""

from __future__ import annotations

import pytest

from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.answer_length_policy import ABSOLUTE_MAX_WORDS

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


@pytest.mark.parametrize("snapshot", ROLE_SNAPSHOTS, ids=[s["title"] for s in ROLE_SNAPSHOTS])
def test_hr_category_present(snapshot: dict) -> None:
    questions = _exportable(_generate(snapshot))
    assert any(q.get("category") == "hr" for q in questions), f"HR missing for {snapshot['title']}"


@pytest.mark.parametrize("snapshot", ROLE_SNAPSHOTS, ids=[s["title"] for s in ROLE_SNAPSHOTS])
def test_daily_routine_present(snapshot: dict) -> None:
    questions = _exportable(_generate(snapshot))
    assert any(q.get("category") == "daily_routine" for q in questions), (
        f"Daily routine missing for {snapshot['title']}"
    )


@pytest.mark.parametrize("snapshot", ROLE_SNAPSHOTS, ids=[s["title"] for s in ROLE_SNAPSHOTS])
def test_seniority_variation_present(snapshot: dict) -> None:
    questions = _exportable(_generate(snapshot))
    blob = " ".join((q.get("question") or "").lower() for q in questions)
    has_seniority = any(
        q.get("question_type") == "seniority"
        or any(k in (q.get("question") or "").lower() for k in ("junior", "senior", "mid-level"))
        for q in questions
    )
    assert has_seniority, f"Seniority variation missing for {snapshot['title']}: {blob[:200]}"


@pytest.mark.parametrize("snapshot", ROLE_SNAPSHOTS, ids=[s["title"] for s in ROLE_SNAPSHOTS])
def test_case_or_practical_present(snapshot: dict) -> None:
    questions = _exportable(_generate(snapshot))
    has_case = any(
        q.get("question_type") in {"case_study", "practical_task"}
        or "case study" in (q.get("question") or "").lower()
        or "practical task" in (q.get("question") or "").lower()
        for q in questions
    )
    assert has_case, f"Case/practical missing for {snapshot['title']}"


@pytest.mark.parametrize("snapshot", ROLE_SNAPSHOTS, ids=[s["title"] for s in ROLE_SNAPSHOTS])
def test_skills_covered(snapshot: dict) -> None:
    questions = _exportable(_generate(snapshot))
    for skill in snapshot["extracted_skills"]:
        covered = any(
            skill.lower() in (q.get("skill_tag") or "").lower()
            or skill.lower() in (q.get("question") or "").lower()
            for q in questions
        )
        assert covered, f"Skill {skill!r} not covered for {snapshot['title']}"


@pytest.mark.parametrize("snapshot", ROLE_SNAPSHOTS, ids=[s["title"] for s in ROLE_SNAPSHOTS])
def test_study_material_for_every_question(snapshot: dict) -> None:
    questions = _exportable(_generate(snapshot))
    assert questions, f"No exportable questions for {snapshot['title']}"
    for q in questions:
        study = q.get("study_material") or {}
        assert study, f"Missing study material for {q.get('question_id')}"
        has_content = (
            study.get("overview")
            or study.get("principles")
            or study.get("step_by_step_breakdown")
            or study.get("what_this_question_tests")
        )
        assert has_content, f"Thin study module for {q.get('question_id')}"


@pytest.mark.parametrize("snapshot", ROLE_SNAPSHOTS, ids=[s["title"] for s in ROLE_SNAPSHOTS])
def test_answers_under_500_words(snapshot: dict) -> None:
    questions = _exportable(_generate(snapshot))
    for q in questions:
        words = len((q.get("model_answer") or "").split())
        assert words <= ABSOLUTE_MAX_WORDS, (
            f"Answer over {ABSOLUTE_MAX_WORDS} words ({words}) for {snapshot['title']} / {q.get('question_id')}"
        )


@pytest.mark.parametrize("snapshot", ROLE_SNAPSHOTS, ids=[s["title"] for s in ROLE_SNAPSHOTS])
def test_behavioral_answers_not_too_short(snapshot: dict) -> None:
    questions = _exportable(_generate(snapshot))
    behavioral = [q for q in questions if q.get("category") == "behavioral"]
    assert behavioral, f"No behavioral questions for {snapshot['title']}"
    short = [q for q in behavioral if len((q.get("model_answer") or "").split()) < 100]
    assert len(short) <= max(1, len(behavioral) // 3), (
        f"Too many short behavioral answers for {snapshot['title']}: {len(short)}/{len(behavioral)}"
    )


def test_no_company_specific_without_company() -> None:
    job = _job(ROLE_SNAPSHOTS[0])
    questions = _exportable(mock_generate_questions(job, focus_areas=["SQL"], difficulty="mid"))
    assert not any(q.get("category") == "company_specific" for q in questions)


def test_company_specific_when_company_provided() -> None:
    job = _job(ROLE_SNAPSHOTS[0])
    job["company_name"] = "Acme Analytics Ltd"
    questions = _exportable(mock_generate_questions(job, focus_areas=["SQL"], difficulty="mid"))
    assert any(q.get("category") == "company_specific" for q in questions)
