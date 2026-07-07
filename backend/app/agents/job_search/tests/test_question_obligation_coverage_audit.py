"""Coverage audit tests for obligation-aware answers and study modules."""

from __future__ import annotations

from app.agents.job_search.knowledge.content_engine import build_model_answer
from app.agents.job_search.knowledge.question_obligations import (
    Obligation,
    QuestionOrigin,
    extract_question_obligations,
    has_intentionally_retained_modifier_obligations,
)
from app.agents.job_search.knowledge.study_material_budget import classify_study_material_depth
from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.question_obligation_coverage_audit import (
    evaluate_answer_obligation_coverage,
    is_answer_obligation_coverage_failure,
    is_pure_motivation_technical_dominance,
    is_study_obligation_coverage_failure,
)

_DEVOPS_JOB = {
    "title": "DevOps Engineer",
    "responsibilities": ["CI/CD pipeline maintenance"],
    "extracted_skills": [{"skill": "AWS"}, {"skill": "CI/CD"}, {"skill": "Docker"}],
}

_HYBRID_Q = {
    "question": (
        "What excites you about this DevOps role, and how would you improve deployment reliability?"
    ),
    "category": "hr",
    "generation_stage_meta": {},
    "obligation_profile": {
        "obligations": [Obligation.MOTIVATION_FIT.value, Obligation.TECHNICAL_METHOD.value],
        "primary_obligation": Obligation.MOTIVATION_FIT.value,
        "origin": QuestionOrigin.SYNTHETIC.value,
        "is_hybrid": True,
        "synthetic_overload": False,
        "overload_reasons": [],
        "evidence_by_obligation": {},
    },
}


def test_pure_motivation_answer_passes() -> None:
    q = {
        "question": "Why are you interested in this Electrical Engineer role?",
        "category": "hr",
        "model_answer": (
            "I am interested in this Electrical Engineer role because the posting centres on load calculations "
            "and the skills listed — especially cable sizing. I want to deepen that work because protection studies "
            "combined with practical distribution design genuinely attract me."
        ),
        "obligation_profile": {
            "obligations": [Obligation.MOTIVATION_FIT.value],
            "primary_obligation": Obligation.MOTIVATION_FIT.value,
            "origin": QuestionOrigin.SYNTHETIC.value,
            "is_hybrid": False,
            "synthetic_overload": False,
            "overload_reasons": [],
            "evidence_by_obligation": {},
        },
    }
    assert evaluate_answer_obligation_coverage(q)["passed"]


def test_pure_motivation_technical_procedure_fails() -> None:
    q = {
        "question": "Why are you interested in this Electrical Engineer role?",
        "category": "hr",
        "model_answer": (
            "I would start by establishing the connected load for every circuit and total it by phase. "
            "Then I would apply demand and diversity factors to convert connected load into realistic maximum demand. "
            "Before closing the task, I would calculate the design current and select a protective device rating."
        ),
        "obligation_profile": {
            "obligations": [Obligation.MOTIVATION_FIT.value],
            "primary_obligation": Obligation.MOTIVATION_FIT.value,
            "origin": QuestionOrigin.SYNTHETIC.value,
            "is_hybrid": False,
            "synthetic_overload": False,
            "overload_reasons": [],
            "evidence_by_obligation": {},
        },
    }
    profile = extract_question_obligations(q)
    assert is_pure_motivation_technical_dominance(q["model_answer"], profile)
    assert not evaluate_answer_obligation_coverage(q)["passed"]


def test_technical_vocabulary_in_motivation_allowed() -> None:
    q = {
        "question": "Why are you interested in this DevOps Engineer role?",
        "category": "hr",
        "model_answer": (
            "I am interested in this DevOps Engineer role because reliable delivery, observability, and CI/CD "
            "automation are areas I genuinely enjoy working on and want to deepen in a team that treats "
            "deployment safety as a product concern."
        ),
        "obligation_profile": {
            "obligations": [Obligation.MOTIVATION_FIT.value],
            "primary_obligation": Obligation.MOTIVATION_FIT.value,
            "origin": QuestionOrigin.SYNTHETIC.value,
            "is_hybrid": False,
            "synthetic_overload": False,
            "overload_reasons": [],
            "evidence_by_obligation": {},
        },
    }
    assert evaluate_answer_obligation_coverage(q)["passed"]


def test_hybrid_answer_covers_motivation_and_method() -> None:
    q = dict(_HYBRID_Q)
    q["model_answer"] = build_model_answer(q, _DEVOPS_JOB)
    result = evaluate_answer_obligation_coverage(q, _DEVOPS_JOB)
    assert result["passed"], result["failures"]


def test_hybrid_motivation_only_answer_fails() -> None:
    q = dict(_HYBRID_Q)
    q["model_answer"] = (
        "I am interested in this DevOps Engineer role because the posting centres on ci/cd pipeline maintenance "
        "and the skills listed — especially AWS, CI/CD, Docker."
    )
    result = evaluate_answer_obligation_coverage(q, _DEVOPS_JOB)
    assert not result["passed"]


def test_hybrid_technical_only_answer_fails() -> None:
    q = dict(_HYBRID_Q)
    q["model_answer"] = (
        "I would start by adding deployment health checks and rollback gates in the pipeline. "
        "Then I would wire monitoring alerts to on-call ownership and verify rollback criteria after each release. "
        "Before closing the task, I would compare failure rate and rollback time against the previous baseline."
    )
    result = evaluate_answer_obligation_coverage(q, _DEVOPS_JOB)
    assert not result["passed"]


def test_technical_explicit_modifier_in_scope_for_canonical_gate() -> None:
    q = {
        "question": (
            "How would you improve deployment reliability in this CI/CD workflow, "
            "which metric would you monitor, and what failure mode would you plan for?"
        ),
        "category": "technical",
        "question_type": "technical_method",
        "model_answer": (
            "I would start by adding pipeline health checks and rollback gates after each deploy. "
            "Then I would wire monitoring alerts to on-call ownership and validate artefacts before promotion."
        ),
    }
    profile = extract_question_obligations(q, _DEVOPS_JOB)
    assert has_intentionally_retained_modifier_obligations(profile)
    assert is_answer_obligation_coverage_failure(q, _DEVOPS_JOB)


def test_passive_metric_hint_not_in_canonical_scope() -> None:
    q = {
        "question": (
            "Describe the most complex production issue you solved using AWS, including impact metrics."
        ),
        "category": "technical",
        "model_answer": "I resolved a pipeline outage by rolling back and fixing the root cause.",
    }
    profile = extract_question_obligations(q, _DEVOPS_JOB)
    assert Obligation.METRIC.value not in profile.obligations
    assert not has_intentionally_retained_modifier_obligations(profile)
    assert not is_answer_obligation_coverage_failure(q, _DEVOPS_JOB)


def test_metric_obligation_requires_measurable_signal() -> None:
    q = {
        "question": "Describe your approach and include one concrete KPI metric.",
        "category": "technical",
        "model_answer": "I would monitor the relevant metric.",
        "obligation_profile": {
            "obligations": [Obligation.TECHNICAL_METHOD.value, Obligation.METRIC.value],
            "primary_obligation": Obligation.TECHNICAL_METHOD.value,
            "origin": QuestionOrigin.SYNTHETIC.value,
            "is_hybrid": True,
            "synthetic_overload": False,
            "overload_reasons": [],
            "evidence_by_obligation": {},
        },
    }
    assert not evaluate_answer_obligation_coverage(q)["passed"]


def test_injected_bad_study_module_fails_gate() -> None:
    q = dict(_HYBRID_Q)
    q["model_answer"] = build_model_answer(q, _DEVOPS_JOB)
    q["study_material"] = {
        "study_depth": "hr_behavioral",
        "step_by_step_method": ["Quote one responsibility from the posting that genuinely interests you."],
        "interview_application": "Keep your answer focused on why the posting attracts you.",
    }
    assert is_study_obligation_coverage_failure(q, _DEVOPS_JOB)


def test_injected_bad_answer_fails_gate() -> None:
    q = dict(_HYBRID_Q)
    q["model_answer"] = "I am passionate, motivated, and eager to contribute."
    assert is_answer_obligation_coverage_failure(q, _DEVOPS_JOB)


def test_employer_hybrid_preserved_and_requires_full_coverage() -> None:
    q = {
        "question": _HYBRID_Q["question"],
        "category": "hr",
        "question_origin": QuestionOrigin.EMPLOYER_PROVIDED.value,
        "model_answer": build_model_answer(
            {**_HYBRID_Q, "question_origin": QuestionOrigin.EMPLOYER_PROVIDED.value}, _DEVOPS_JOB
        ),
    }
    profile = extract_question_obligations(q, _DEVOPS_JOB)
    assert profile.origin == QuestionOrigin.EMPLOYER_PROVIDED.value
    assert profile.synthetic_overload is False
    assert evaluate_answer_obligation_coverage(q, _DEVOPS_JOB)["passed"]


def test_technical_load_calculation_not_flagged_as_pure_motivation_dominance() -> None:
    q = {
        "question": "How would you perform load calculations for a new LV distribution board?",
        "category": "technical",
        "skill_tag": "Load Calculations",
        "model_answer": (
            "I would establish the connected load for every circuit and total it by phase, apply diversity factors, "
            "calculate design current, and verify cable capacity and voltage drop against BS 7671 limits."
        ),
    }
    assert not is_answer_obligation_coverage_failure(q, {"title": "Electrical Engineer"})


def test_hybrid_depth_not_collapsed_to_hr_only() -> None:
    depth = classify_study_material_depth(_HYBRID_Q, _DEVOPS_JOB)
    assert depth != "hr_behavioral"


def test_devops_pack_obligation_metrics_clean() -> None:
    questions = mock_generate_questions(_DEVOPS_JOB, focus_areas=["AWS", "CI/CD"], difficulty="mid")
    failures = sum(1 for q in questions if is_answer_obligation_coverage_failure(q, _DEVOPS_JOB))
    assert failures == 0
