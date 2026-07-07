"""Unit tests for multi-obligation extraction and synthetic overload handling."""

from __future__ import annotations

import pytest

from app.agents.job_search.knowledge.question_obligations import (
    Obligation,
    QuestionOrigin,
    detect_synthetic_overload,
    extract_question_obligations,
    repair_synthetic_question_overload,
    resolve_question_origin,
    segment_question_clauses,
    split_synthetic_overloaded_question,
)
from app.agents.job_search.mock_data import mock_generate_questions

_DEVOPS_OVERLOADED = (
    "Why are you interested in this DevOps Engineer, and how would you improve reliable "
    "deployments, monitoring, incident response, and secure infrastructure automation using "
    "tools such as AWS, CI/CD, Docker, Kubernetes? In this role-specific case, address: "
    "DevOps Engineer context: CI/CD pipeline maintenance. Include one concrete core competency "
    "metric, one governing standard/protocol, and one failure mode relevant to DevOps Engineer "
    "context: CI/CD pipeline maintenance."
)

_NINE_CASES = [
    (
        "Data Analyst",
        "Why do you want this Data Analyst, and how would you turn messy operational data into trusted SQL queries, dashboards, and KPI reporting with clear data quality checks that stakeholders can act on?",
        {"motivation_fit", "technical_method"},
    ),
    (
        "Clinical Pharmacist",
        "Why do you want this Clinical Pharmacist, and how would you contribute to medicines optimisation through medication review, prescribing safety checks, patient counselling, and clinical governance?",
        {"motivation_fit", "contribution"},
    ),
    (
        "Barista",
        "Why do you want this Barista, and how would you keep drink quality, hygiene, allergen control, and customer service consistent during busy rush periods?",
        {"motivation_fit", "technical_method", "scenario_reasoning"},
    ),
    (
        "Teaching Assistant",
        "Why do you want this Teaching Assistant, and which strengths in Classroom Support, Safeguarding, Communication would help you deliver the responsibilities listed in this posting from the first month?",
        {"motivation_fit", "strengths", "contribution"},
    ),
    (
        "Financial Analyst",
        "Why do you want this Financial Analyst, and which strengths in Financial Modelling, Excel would help you deliver the responsibilities listed in this posting from the first month?",
        {"motivation_fit", "strengths", "contribution"},
    ),
    (
        "DevOps Engineer",
        "Why are you interested in this DevOps Engineer, and how would you improve reliable deployments, monitoring, incident response, and secure infrastructure automation using tools such as AWS, CI/CD, Docker, Kubernetes?",
        {"motivation_fit", "technical_method"},
    ),
    (
        "MEP Site Engineer",
        "Why do you want this MEP Site Engineer, and which strengths in MEP Coordination, Site Supervision would help you deliver the responsibilities listed in this posting from the first month?",
        {"motivation_fit", "strengths", "contribution"},
    ),
    (
        "Social Media Creator",
        "Why do you want this Social Media Creator, and which strengths in Video Editing, Content Planning would help you deliver the responsibilities listed in this posting from the first month?",
        {"motivation_fit", "strengths", "contribution"},
    ),
    (
        "Delivery Driver",
        "Why do you want this Delivery Driver, and which strengths in Route Planning, Customer Service would help you deliver the responsibilities listed in this posting from the first month?",
        {"motivation_fit", "strengths", "contribution"},
    ),
]


def test_pure_motivation_clause_extraction() -> None:
    q = {"question": "Why are you interested in this Electrical Engineer role?", "category": "hr"}
    profile = extract_question_obligations(q, {})
    assert profile.obligations == (Obligation.MOTIVATION_FIT.value,)
    assert profile.is_hybrid is False
    assert profile.synthetic_overload is False


def test_hybrid_motivation_technical_clause_extraction() -> None:
    q = {
        "question": (
            "What excites you about this DevOps role, and how would you improve deployment reliability?"
        ),
        "category": "hr",
        "generation_stage_meta": {},
    }
    profile = extract_question_obligations(q, {})
    assert Obligation.MOTIVATION_FIT.value in profile.obligations
    assert Obligation.TECHNICAL_METHOD.value in profile.obligations
    assert profile.is_hybrid is True


def test_hybrid_motivation_contribution_extraction() -> None:
    q = {
        "question": "Why are you interested in the role, and what would you contribute in the first month?",
        "category": "hr",
    }
    profile = extract_question_obligations(q, {})
    assert {Obligation.MOTIVATION_FIT.value, Obligation.CONTRIBUTION.value}.issubset(set(profile.obligations))


def test_hybrid_motivation_scenario_extraction() -> None:
    q = {
        "question": (
            "Why are you interested in the role, and how would you handle conflicting safety and delivery constraints?"
        ),
        "category": "hr",
    }
    profile = extract_question_obligations(q, {})
    assert Obligation.MOTIVATION_FIT.value in profile.obligations
    assert Obligation.SCENARIO_REASONING.value in profile.obligations


def test_explicit_metric_obligation_only_when_asked() -> None:
    q = {"question": "Include one concrete KPI metric you would track for dashboard freshness.", "category": "technical"}
    profile = extract_question_obligations(q, {})
    assert Obligation.METRIC.value in profile.obligations


def test_synthetic_overload_detected_for_devops_hybrid() -> None:
    from app.agents.job_search.knowledge.question_obligations import mark_synthetic_question

    q = mark_synthetic_question({"question": _DEVOPS_OVERLOADED, "category": "hr"})
    profile = extract_question_obligations(q, {})
    assert profile.synthetic_overload is True
    assert "motivation_plus_technical_method" in profile.overload_reasons


def test_employer_provided_hybrid_not_overload() -> None:
    q = {
        "question": _DEVOPS_OVERLOADED,
        "category": "hr",
        "question_origin": QuestionOrigin.EMPLOYER_PROVIDED.value,
    }
    profile = extract_question_obligations(q, {})
    assert profile.synthetic_overload is False
    assert profile.origin == QuestionOrigin.EMPLOYER_PROVIDED.value


def test_unknown_origin_not_treated_as_synthetic_for_rewrite() -> None:
    q = {"question": _DEVOPS_OVERLOADED, "category": "hr"}
    assert resolve_question_origin(q) == QuestionOrigin.UNKNOWN.value
    repaired = repair_synthetic_question_overload([q], {})[0]
    assert repaired["question"] == _DEVOPS_OVERLOADED


def test_split_synthetic_overloaded_question_produces_atomic_units() -> None:
    from app.agents.job_search.knowledge.question_obligations import mark_synthetic_question

    job = {
        "title": "DevOps Engineer",
        "responsibilities": ["CI/CD pipeline maintenance"],
        "extracted_skills": [{"skill": "AWS"}, {"skill": "CI/CD"}],
    }
    q = mark_synthetic_question({"question": _DEVOPS_OVERLOADED, "category": "hr"})
    splits = split_synthetic_overloaded_question(q, job)
    assert len(splits) == 2
    texts = " ".join(s["question"].lower() for s in splits)
    assert "why are you interested" in texts
    assert "how would you" in texts
    assert "include one concrete" not in texts


@pytest.mark.parametrize("role,question,expected_major", _NINE_CASES)
def test_nine_known_role_obligations(role: str, question: str, expected_major: set[str]) -> None:
    q = {"question": question, "category": "hr", "generation_stage_meta": {}}
    profile = extract_question_obligations(q, {"title": role})
    assert expected_major.issubset(set(profile.obligations)), f"{role}: {profile.obligations}"


def test_repair_pipeline_removes_synthetic_overload_from_generated_hr() -> None:
    from app.agents.job_search.knowledge.question_obligations import mark_synthetic_question

    job = {
        "title": "DevOps Engineer",
        "responsibilities": ["CI/CD pipeline maintenance"],
        "requirements": ["AWS"],
        "extracted_skills": [{"skill": "AWS"}, {"skill": "CI/CD"}, {"skill": "Docker"}],
    }
    raw = [mark_synthetic_question({"category": "hr", "question": _DEVOPS_OVERLOADED})]
    repaired = repair_synthetic_question_overload(raw, job)
    assert len(repaired) >= 2
    for item in repaired:
        p = extract_question_obligations(item, job)
        assert not p.synthetic_overload


def test_generated_pack_hr_motivation_no_longer_overloaded() -> None:
    job = {
        "title": "DevOps Engineer",
        "responsibilities": ["CI/CD pipeline maintenance"],
        "extracted_skills": [{"skill": "AWS"}, {"skill": "CI/CD"}, {"skill": "Docker"}],
    }
    questions = mock_generate_questions(job, focus_areas=["AWS", "CI/CD"], difficulty="mid")
    hr = [q for q in questions if q.get("category") == "hr" and "why are you interested" in (q.get("question") or "").lower()]
    assert hr, "expected atomic HR motivation question"
    for q in hr:
        profile = extract_question_obligations(q, job)
        assert not profile.synthetic_overload
        assert "and how would you improve reliable deployments" not in (q.get("question") or "").lower()


def test_segment_question_clauses_preserves_compound_terms() -> None:
    clauses = segment_question_clauses(
        "Why do you want this role, and how would you improve CI/CD pipeline reliability?"
    )
    assert len(clauses) >= 2
    assert any("ci/cd" in c.lower() for c in clauses)


def test_detect_overload_allows_strengths_plus_motivation() -> None:
    overload, reasons = detect_synthetic_overload(
        (Obligation.MOTIVATION_FIT.value, Obligation.STRENGTHS.value),
        origin=QuestionOrigin.SYNTHETIC.value,
    )
    assert overload is False
    assert reasons == ()
