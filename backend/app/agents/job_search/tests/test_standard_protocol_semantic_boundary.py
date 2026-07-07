"""Five-case semantic boundary matrix for standard/protocol obligation coverage."""

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
from app.agents.job_search.quality.question_obligation_coverage_audit import (
    audit_question_obligations,
    evaluate_answer_obligation_coverage,
)

_ELECTRICAL_JOB = {
    "title": "Electrical Engineer",
    "responsibilities": ["LV installation design"],
    "extracted_skills": [{"skill": "Load Calculations"}, {"skill": "Cable Sizing"}],
}

_METHOD_WITHOUT_STANDARD = (
    "I would review the load, determine demand and diversity, size the distribution equipment, "
    "check voltage drop and coordinate protection."
)

_WEAK_STANDARD_ANSWER = "I would follow the relevant standards."


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


def test_standard_boundary_a_incidental_context_stays_canonically_clean() -> None:
    """Case A — IEC standards describe project context, not an independently demanded obligation."""
    q = {
        "question": (
            "Tell me about your experience working on electrical projects governed by IEC standards."
        ),
        "category": "hr",
        "question_type": "hr_behavioral",
        "model_answer": (
            "I spent two years on commercial fit-outs coordinating cable routes, panel schedules, "
            "and handover packs with the site team."
        ),
        "study_material": {"study_depth": "hr_behavioral"},
    }
    profile = extract_question_obligations(q, _ELECTRICAL_JOB)
    assert Obligation.STANDARD_OR_PROTOCOL.value not in profile.obligations
    assert not has_intentionally_retained_modifier_obligations(profile)
    assert not question_in_obligation_audit_scope(q, profile)

    obligation_metrics, _metrics, all_clean, reasons = _audit_canonical_pack(q, _ELECTRICAL_JOB)
    assert obligation_metrics["answer_obligation_coverage_failure_count"] == 0
    assert obligation_metrics["study_obligation_coverage_failure_count"] == 0
    assert all_clean is True
    assert "answer_obligation_coverage_failure_count" not in reasons


def test_standard_boundary_b_explicit_required_standard_fails_canonical_pack() -> None:
    """Case B — explicit standard choice is demanded and weak generic coverage must not pass."""
    q = {
        "question": (
            "Which electrical standard would you apply when designing this LV installation, and why?"
        ),
        "category": "technical",
        "question_type": "technical_method",
        "skill_tag": "Load Calculations",
        "model_answer": _METHOD_WITHOUT_STANDARD,
        "study_material": {
            "study_depth": "standard_technical",
            "step_by_step_method": ["Review connected load and apply diversity factors."],
        },
    }
    profile = extract_question_obligations(q, _ELECTRICAL_JOB)
    assert Obligation.STANDARD_OR_PROTOCOL.value in profile.obligations
    assert has_intentionally_retained_modifier_obligations(profile)
    assert question_in_obligation_audit_scope(q, profile)

    eval_result = evaluate_answer_obligation_coverage(q, _ELECTRICAL_JOB)
    assert not eval_result["passed"]
    assert Obligation.STANDARD_OR_PROTOCOL.value in eval_result["missing_obligations"]

    obligation_metrics, _metrics, all_clean, reasons = _audit_canonical_pack(q, _ELECTRICAL_JOB)
    assert obligation_metrics["answer_obligation_coverage_failure_count"] > 0
    assert all_clean is False
    assert "answer_obligation_coverage_failure_count" in reasons

    weak = dict(q, model_answer=_WEAK_STANDARD_ANSWER)
    weak_eval = evaluate_answer_obligation_coverage(weak, _ELECTRICAL_JOB)
    assert not weak_eval["passed"]
    assert Obligation.STANDARD_OR_PROTOCOL.value in weak_eval["missing_obligations"]


def test_standard_boundary_c_embedded_protocol_fails_canonical_pack() -> None:
    """Case C — embedded escalation protocol demand must fail when answer omits procedural basis."""
    q = {
        "question": (
            "Explain how you would handle the incident, including the escalation protocol you would "
            "follow if the first response failed."
        ),
        "category": "technical",
        "question_type": "scenario",
        "model_answer": (
            "I would assess the impact, contain the blast radius, communicate status to stakeholders, "
            "and monitor recovery until service is stable."
        ),
        "study_material": {
            "study_depth": "complex_scenario",
            "step_by_step_method": ["Assess impact.", "Contain blast radius."],
        },
    }
    profile = extract_question_obligations(q, _ELECTRICAL_JOB)
    assert Obligation.SCENARIO_REASONING.value in profile.obligations
    assert Obligation.STANDARD_OR_PROTOCOL.value in profile.obligations
    assert has_intentionally_retained_modifier_obligations(profile)

    obligation_metrics, _metrics, all_clean, reasons = _audit_canonical_pack(q, _ELECTRICAL_JOB)
    assert obligation_metrics["answer_obligation_coverage_failure_count"] > 0
    assert all_clean is False
    assert "answer_obligation_coverage_failure_count" in reasons


def test_standard_boundary_d_employer_embedded_standard_fails_canonical_pack() -> None:
    """Case D — employer-provided embedded standard requirement is preserved and enforced."""
    question_text = (
        "How would you design and verify the installation, including the standard you would apply "
        "and the evidence you would retain for compliance?"
    )
    q = {
        "question": question_text,
        "category": "technical",
        "question_type": "technical_method",
        "question_origin": QuestionOrigin.EMPLOYER_PROVIDED.value,
        "skill_tag": "Load Calculations",
        "model_answer": _METHOD_WITHOUT_STANDARD,
        "study_material": {
            "study_depth": "standard_technical",
            "step_by_step_method": ["Review connected load and apply diversity factors."],
        },
    }
    profile = extract_question_obligations(q, _ELECTRICAL_JOB)
    assert profile.origin == QuestionOrigin.EMPLOYER_PROVIDED.value
    assert profile.synthetic_overload is False
    assert q["question"] == question_text
    assert Obligation.STANDARD_OR_PROTOCOL.value in profile.obligations
    assert Obligation.TECHNICAL_METHOD.value in profile.obligations
    assert has_intentionally_retained_modifier_obligations(profile)

    obligation_metrics, _metrics, all_clean, reasons = _audit_canonical_pack(q, _ELECTRICAL_JOB)
    assert obligation_metrics["answer_obligation_coverage_failure_count"] > 0
    assert all_clean is False
    assert "answer_obligation_coverage_failure_count" in reasons


def test_standard_boundary_e_synthetic_forced_overload_not_false_clean() -> None:
    """Case E — synthetic forced modifier stacking must not produce false clean."""
    raw = mark_synthetic_question(
        {
            "question": (
                "Why are you interested in this role, and how would you perform the work including "
                "a metric, protocol, standard, and failure mode?"
            ),
            "category": "hr",
        }
    )
    profile = extract_question_obligations(raw, _ELECTRICAL_JOB)
    assert profile.origin == QuestionOrigin.SYNTHETIC.value
    assert profile.synthetic_overload is True

    unrepaired = dict(
        raw,
        model_answer="I am interested because the role aligns with my goals.",
        study_material={"study_depth": "hr_behavioral"},
    )
    obligation_metrics, _metrics, all_clean, reasons = _audit_canonical_pack(unrepaired, _ELECTRICAL_JOB)
    assert obligation_metrics["synthetic_overload_failure_count"] > 0
    assert all_clean is False
    assert "synthetic_overload_failure_count" in reasons

    repaired = repair_synthetic_question_overload([raw], _ELECTRICAL_JOB)
    assert len(repaired) >= 2
    for item in repaired:
        assert not extract_question_obligations(item, _ELECTRICAL_JOB).synthetic_overload


def test_standard_boundary_study_omission_blocks_canonical_clean() -> None:
    """Study module must teach demanded standard/protocol basis, not generic compliance language."""
    q = {
        "question": (
            "Which electrical standard would you apply when designing this LV installation, and why?"
        ),
        "category": "technical",
        "question_type": "technical_method",
        "model_answer": (
            "I would apply BS 7671 when designing this LV installation because it governs cable sizing, "
            "protection coordination, and verification evidence for domestic and commercial installations."
        ),
        "study_material": {
            "study_depth": "standard_technical",
            "step_by_step_method": ["Follow relevant standards and procedures when sizing the installation."],
        },
    }
    profile = extract_question_obligations(q, _ELECTRICAL_JOB)
    assert Obligation.STANDARD_OR_PROTOCOL.value in profile.obligations

    obligation_metrics, _metrics, all_clean, reasons = _audit_canonical_pack(q, _ELECTRICAL_JOB)
    assert obligation_metrics["study_obligation_coverage_failure_count"] > 0
    assert all_clean is False
    assert "study_obligation_coverage_failure_count" in reasons
