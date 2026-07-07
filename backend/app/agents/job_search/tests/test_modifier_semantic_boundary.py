"""Four-case semantic boundary matrix for modifier obligation retention (A–D gate)."""

from __future__ import annotations

from app.agents.job_search.knowledge.question_obligations import (
    Obligation,
    QuestionOrigin,
    extract_question_obligations,
    has_intentionally_retained_modifier_obligations,
    mark_synthetic_question,
    question_in_obligation_audit_scope,
    repair_synthetic_question_overload,
)
from app.agents.job_search.quality.final_regression_audit import metrics_are_clean, pack_failure_reasons
from app.agents.job_search.quality.question_obligation_coverage_audit import audit_question_obligations
from app.agents.job_search.tests.test_question_obligations import _DEVOPS_OVERLOADED

_DEVOPS_JOB = {
    "title": "DevOps Engineer",
    "responsibilities": ["CI/CD pipeline maintenance"],
    "extracted_skills": [{"skill": "CI/CD"}, {"skill": "AWS"}],
}

_METHOD_ONLY_ANSWER = (
    "I would start by adding pipeline health checks and rollback gates after each deploy. "
    "Then I would wire monitoring alerts to on-call ownership and validate artefacts before promotion. "
    "After that, I would compare deployment outcomes against the previous baseline before closing the change."
)


def _canonical_metrics_stub() -> dict:
    return {
        "missing_answer_count": 0,
        "missing_study_module_count": 0,
        "fake_url_hits": 0,
        "generic_phrase_hits": 0,
        "silly_question_hits": 0,
        "empty_section_count": 0,
        "hard_max_violation_count": 0,
        "missing_study_depth_count": 0,
        "answers_over_limit_count": 0,
        "duplicate_study_module_count": 0,
        "internal_label_leak_count": 0,
        "unsupported_personal_claim_count": 0,
        "unsupported_numeric_claim_count": 0,
        "cross_domain_contamination_hits": 0,
        "surface_quality_defect_count": 0,
        "thin_input_specificity_violation_count": 0,
        "structure_incomplete_count": 0,
        "substantive_depth_failure_count": 0,
        "intent_depth_mismatch_count": 0,
        "question_study_alignment_failure_count": 0,
        "source_ladder_present": True,
        "export_ready": True,
        "question_count": 1,
        "coverage_score": 0,
    }


def _audit_canonical_pack(question: dict, job: dict) -> tuple[dict, dict, bool, list[str]]:
    obligation_metrics = audit_question_obligations([question], job)
    metrics = _canonical_metrics_stub()
    metrics.update(obligation_metrics)
    clean = metrics_are_clean(metrics, allow_thin_coverage=True)
    reasons = pack_failure_reasons(metrics, allow_thin_coverage=True)
    return obligation_metrics, metrics, clean, reasons


def test_boundary_a_incidental_metric_mention_stays_canonically_clean() -> None:
    """Case A — metrics mentioned as background context, not a demanded deliverable."""
    q = {
        "question": (
            "Tell me about your experience working with dashboards that included impact metrics "
            "for operational reporting."
        ),
        "category": "hr",
        "question_type": "hr_behavioral",
        "model_answer": (
            "In my previous role I built weekly operational dashboards for the logistics team. "
            "The reports helped managers spot delivery delays and staffing gaps without needing ad hoc spreadsheets."
        ),
        "study_material": {"study_depth": "hr_behavioral"},
    }
    profile = extract_question_obligations(q, _DEVOPS_JOB)
    assert Obligation.METRIC.value not in profile.obligations
    assert not has_intentionally_retained_modifier_obligations(profile)
    assert not question_in_obligation_audit_scope(q, profile)

    obligation_metrics, _metrics, all_clean, reasons = _audit_canonical_pack(q, _DEVOPS_JOB)
    assert obligation_metrics["answer_obligation_coverage_failure_count"] == 0
    assert all_clean is True
    assert "answer_obligation_coverage_failure_count" not in reasons


def test_boundary_b_embedded_required_metric_fails_canonical_pack() -> None:
    """Case B — embedded but genuinely required metric on a non-HR technical question."""
    q = {
        "question": (
            "Explain how you would improve deployment reliability, including the impact metric "
            "you would monitor to verify the change."
        ),
        "category": "technical",
        "question_type": "technical_method",
        "skill_tag": "CI/CD",
        "model_answer": _METHOD_ONLY_ANSWER,
        "study_material": {"study_depth": "standard_technical"},
    }
    profile = extract_question_obligations(q, _DEVOPS_JOB)
    assert Obligation.TECHNICAL_METHOD.value in profile.obligations
    assert Obligation.METRIC.value in profile.obligations
    assert has_intentionally_retained_modifier_obligations(profile)
    assert question_in_obligation_audit_scope(q, profile)

    obligation_metrics, _metrics, all_clean, reasons = _audit_canonical_pack(q, _DEVOPS_JOB)
    assert obligation_metrics["answer_obligation_coverage_failure_count"] > 0
    assert all_clean is False
    assert "answer_obligation_coverage_failure_count" in reasons


def test_boundary_c_synthetic_forced_overload_not_false_clean() -> None:
    """Case C — synthetic forced overload must hard-fail or be repaired, never false-clean."""
    raw = mark_synthetic_question({"question": _DEVOPS_OVERLOADED, "category": "hr"})
    profile = extract_question_obligations(raw, _DEVOPS_JOB)
    assert profile.origin == QuestionOrigin.SYNTHETIC.value
    assert profile.synthetic_overload is True
    assert "motivation_plus_forced_modifiers" in profile.overload_reasons

    unrepaired = dict(
        raw,
        model_answer="I am interested in this DevOps Engineer role because reliable delivery matters to me.",
        study_material={"study_depth": "hr_behavioral"},
    )
    obligation_metrics, _metrics, all_clean, reasons = _audit_canonical_pack(unrepaired, _DEVOPS_JOB)
    assert obligation_metrics["synthetic_overload_failure_count"] > 0
    assert all_clean is False
    assert "synthetic_overload_failure_count" in reasons

    repaired = repair_synthetic_question_overload([raw], _DEVOPS_JOB)
    assert len(repaired) >= 2
    for item in repaired:
        repaired_profile = extract_question_obligations(item, _DEVOPS_JOB)
        assert not repaired_profile.synthetic_overload


def test_boundary_d_employer_embedded_modifiers_fails_canonical_pack() -> None:
    """Case D — employer-provided embedded modifier requirements are preserved and enforced."""
    q = {
        "question": (
            "How would you improve deployment reliability, including the metric you would track "
            "and the main failure mode you would prepare for?"
        ),
        "category": "technical",
        "question_type": "technical_method",
        "question_origin": QuestionOrigin.EMPLOYER_PROVIDED.value,
        "skill_tag": "CI/CD",
        "model_answer": _METHOD_ONLY_ANSWER,
        "study_material": {"study_depth": "standard_technical"},
    }
    profile = extract_question_obligations(q, _DEVOPS_JOB)
    assert profile.origin == QuestionOrigin.EMPLOYER_PROVIDED.value
    assert profile.synthetic_overload is False
    assert Obligation.TECHNICAL_METHOD.value in profile.obligations
    assert Obligation.METRIC.value in profile.obligations
    assert Obligation.FAILURE_MODE.value in profile.obligations
    assert q["question"] == (
        "How would you improve deployment reliability, including the metric you would track "
        "and the main failure mode you would prepare for?"
    )
    assert has_intentionally_retained_modifier_obligations(profile)
    assert question_in_obligation_audit_scope(q, profile)

    obligation_metrics, _metrics, all_clean, reasons = _audit_canonical_pack(q, _DEVOPS_JOB)
    assert obligation_metrics["answer_obligation_coverage_failure_count"] > 0
    assert all_clean is False
    assert "answer_obligation_coverage_failure_count" in reasons
