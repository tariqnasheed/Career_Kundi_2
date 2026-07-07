"""004E-E2 / 004E-E2.1 adaptive study-material depth and length policy tests."""

from __future__ import annotations

import re

import pytest

from app.agents.job_search.knowledge.question_study_material import apply_finalized_study_module
from app.agents.job_search.knowledge.study_material_budget import (
    _BUDGETS,
    apply_adaptive_study_budget,
    classify_study_material_depth,
    collect_complexity_signals,
    count_words,
    evaluate_budget_status,
    evaluate_depth_contract,
    is_job_thin,
    is_thin_conservative_input,
    resolve_study_material_budget,
    shape_study_module_by_depth,
    study_module_core_word_count,
)
from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.answer_length_policy import ABSOLUTE_MAX_WORDS
from app.agents.job_search.quality.blocked_phrase_guard import export_blocked_phrase_count
from app.core.config import settings


def _q(**kwargs: object) -> dict:
    base = {
        "question_id": "TEST-001",
        "question": "Sample question?",
        "category": "technical",
        "question_type": "technical",
        "skill_tag": "SQL",
        "model_answer": "A" * 50,
        "study_material": {
            "core_idea": "Core teaching point for the question.",
            "what_this_question_tests": "Tests applied understanding.",
            "beginner_explanation": "Beginner layer explanation with concrete terms.",
            "intermediate_explanation": "Intermediate layer with workflow and checks.",
            "advanced_explanation": "Advanced nuance for experienced practitioners.",
            "key_principles": ["Principle one", "Principle two"],
            "step_by_step_method": ["Step one", "Step two", "Step three"],
            "common_mistakes": ["Mistake one", "Mistake two"],
            "interview_application": "How to apply this in the interview room.",
        },
    }
    base.update(kwargs)
    return base


def _job(**kwargs: object) -> dict:
    base = {
        "title": "Data Analyst",
        "description_raw": "Dashboards and reporting.",
        "responsibilities": ["Build dashboards"],
        "requirements": ["SQL"],
        "extracted_skills": [{"skill": "SQL"}],
    }
    base.update(kwargs)
    return base


def _first_study(job: dict, focus: list[str] | None = None, *, depth: str | None = None) -> dict:
    questions = mock_generate_questions(job, focus_areas=focus or [], difficulty="mid")
    exportable = [q for q in questions if q.get("model_answer") and not q.get("export_blocked")]
    if depth:
        for q in exportable:
            study = q.get("study_material") or {}
            if study.get("study_depth") == depth:
                return study
    return (exportable[0].get("study_material") or {}) if exportable else {}


@pytest.mark.parametrize(
    ("question", "job", "expected"),
    [
        (_q(question="What is SQL?", category="technical"), _job(), "simple_factual"),
        (
            _q(question="Why do you want this role?", category="hr", question_type="motivation"),
            _job(),
            "hr_behavioral",
        ),
        (
            _q(question="Explain how joins work in relational databases.", category="technical"),
            _job(),
            "standard_technical",
        ),
        (
            _q(question="How would you use Power BI to debug a broken dashboard?", question_type="tool_usage"),
            _job(),
            "practical_workflow",
        ),
        (
            _q(
                question="Walk through a medication safety scenario when a near-miss occurs on the ward.",
                category="technical",
            ),
            _job(title="Clinical Pharmacist"),
            "complex_scenario",
        ),
        (
            _q(
                question="Design a multi-region system architecture with trade-offs for scalability and compliance.",
                category="technical",
            ),
            _job(title="Senior Systems Engineer"),
            "advanced_multi_step",
        ),
    ],
)
def test_depth_classification(question: dict, job: dict, expected: str) -> None:
    assert classify_study_material_depth(question, job) == expected


@pytest.mark.parametrize(
    ("depth", "hard_max"),
    [
        ("simple_factual", 350),
        ("hr_behavioral", 450),
        ("standard_technical", 850),
        ("practical_workflow", 950),
        ("complex_scenario", 1100),
        ("advanced_multi_step", 1200),
    ],
)
def test_hard_max_per_category(depth: str, hard_max: int) -> None:
    assert _BUDGETS[depth].hard_max_words == hard_max


def test_simple_factual_stays_economical() -> None:
    study = _first_study(
        {"title": "Teaching Assistant", "responsibilities": ["Classroom support"], "extracted_skills": [{"skill": "Classroom Support"}]},
        ["Classroom Support"],
        depth="simple_factual",
    )
    assert study.get("compact_explanation")
    assert not study.get("beginner_explanation")
    assert study["actual_word_count"] < study["hard_max_words"] * 0.8


def test_hr_behavioral_avoids_hard_ceiling_attraction() -> None:
    studies = []
    job = {"title": "HR Assistant", "responsibilities": ["Employee onboarding"], "extracted_skills": [{"skill": "Onboarding"}]}
    for q in mock_generate_questions(job, focus_areas=["Onboarding"], difficulty="mid"):
        if not q.get("model_answer") or q.get("export_blocked"):
            continue
        study = q.get("study_material") or {}
        if study.get("study_depth") == "hr_behavioral":
            studies.append(study)
    assert studies
    for study in studies:
        assert study.get("behavioral_response_structure")
        assert study["actual_word_count"] <= study["hard_max_words"] * 0.75


def test_practical_workflow_has_workflow_structure() -> None:
    study = _first_study(
        {"title": "DevOps Engineer", "responsibilities": ["CI/CD pipeline maintenance"], "extracted_skills": [{"skill": "CI/CD"}]},
        ["CI/CD"],
        depth="practical_workflow",
    )
    assert study.get("workflow_objective")
    assert len(study.get("step_by_step_method") or []) >= 4
    assert study.get("workflow_checkpoints")
    assert study.get("failure_modes")
    assert study.get("escalation_triggers")


def test_complex_scenario_has_branches_and_tradeoffs() -> None:
    study = _first_study(
        {"title": "Clinical Pharmacist", "responsibilities": ["Medication review"], "extracted_skills": [{"skill": "Medication Review"}]},
        ["Medication Review"],
        depth="complex_scenario",
    )
    assert study.get("scenario_framing")
    assert study.get("competing_constraints")
    assert study.get("decision_branches")
    assert study.get("verification_steps")


def test_advanced_multi_step_has_staged_structure() -> None:
    study = _first_study(
        {"title": "Senior Systems Engineer", "responsibilities": ["System architecture"], "extracted_skills": [{"skill": "System Design"}]},
        ["System Design"],
        depth="advanced_multi_step",
    )
    assert study.get("system_framing")
    assert study.get("assumptions_and_dependencies")
    assert study.get("staged_reasoning")
    assert study.get("trade_off_analysis")
    assert study.get("validation_and_monitoring")


def test_title_only_zero_source_is_conservative() -> None:
    job = {"title": "Mystery Role"}
    studies = [
        (q.get("study_material") or {})
        for q in mock_generate_questions(job, focus_areas=[], difficulty="auto")
        if q.get("model_answer") and not q.get("export_blocked")
    ]
    assert studies
    for study in studies:
        assert study.get("thin_input_conservative") is True
        assert study["actual_word_count"] <= 220
        assert "advanced_multi_step" != study.get("study_depth")


def test_concise_complete_requires_substantive_coverage_for_deep_depths() -> None:
    budget = _BUDGETS["advanced_multi_step"]
    assert (
        evaluate_budget_status(
            400,
            budget,
            contract_coverage=0.9,
            substantive_coverage=0.95,
            integrity_clean=True,
        )
        == "concise_complete"
    )
    assert (
        evaluate_budget_status(
            400,
            budget,
            contract_coverage=0.9,
            substantive_coverage=0.4,
            integrity_clean=True,
        )
        == "structure_incomplete"
    )
    assert (
        evaluate_budget_status(
            400,
            budget,
            contract_coverage=0.9,
            substantive_coverage=0.95,
            integrity_clean=False,
        )
        == "structure_incomplete"
    )


def test_controlled_simple_vs_advanced_differentiation() -> None:
    simple_q = _q(question="What is load balancing?", category="technical", skill_tag="Load Balancing")
    advanced_q = _q(
        question="Design a multi-region load balancing architecture with trade-offs for scalability and compliance.",
        category="technical",
        skill_tag="Load Balancing",
    )
    job = _job(title="Senior Systems Engineer")
    simple_study = apply_adaptive_study_budget(simple_q["study_material"], simple_q, job)
    advanced_study = apply_adaptive_study_budget(advanced_q["study_material"], advanced_q, job)
    assert simple_study["study_depth"] == "simple_factual"
    assert advanced_study["study_depth"] == "advanced_multi_step"
    assert advanced_study.get("staged_reasoning")
    assert not simple_study.get("staged_reasoning")
    assert evaluate_depth_contract(advanced_study, "advanced_multi_step")["depth_contract_coverage"] >= 0.8
    assert advanced_study["actual_word_count"] > simple_study["actual_word_count"]


def test_no_hard_max_violation_on_generated_packs() -> None:
    job = _job()
    questions = mock_generate_questions(job, focus_areas=["SQL"], difficulty="mid")
    for q in questions:
        if not q.get("model_answer") or q.get("export_blocked"):
            continue
        study = q.get("study_material") or {}
        assert study.get("study_depth")
        assert int(study.get("actual_word_count") or 0) <= int(study.get("hard_max_words") or 0)


def test_no_mid_sentence_truncation_marker() -> None:
    oversized = dict(_q()["study_material"])
    oversized["advanced_explanation"] = " ".join(["Sentence one here.", "Sentence two here.", "Sentence three here."] * 80)
    study = apply_adaptive_study_budget(oversized, _q(), _job())
    for key in ("advanced_explanation", "intermediate_explanation", "core_idea", "compact_explanation"):
        text = str(study.get(key) or "")
        if text:
            assert not text.endswith(" wor")
            assert not re.search(r"\b\w+,$", text)
            assert text[-1] in ".!?" or text.endswith("]")


def test_evaluate_budget_status_semantics() -> None:
    budget = _BUDGETS["standard_technical"]
    assert evaluate_budget_status(200, budget, contract_coverage=0.9, substantive_coverage=0.9) == "concise_complete"
    assert evaluate_budget_status(500, budget, contract_coverage=0.9, substantive_coverage=0.9) == "within_target"
    assert evaluate_budget_status(800, budget, contract_coverage=0.9, substantive_coverage=0.9) == "above_target_but_allowed"
    assert evaluate_budget_status(900, budget, contract_coverage=0.9, substantive_coverage=0.9) == "hard_limit_exceeded"


def test_title_only_complex_question_keeps_intent_depth() -> None:
    """Thinness controls conservatism/length, NOT the depth category: a complex
    scenario/behavioral question must not be mislabelled simple_factual."""
    scenario_q = _q(
        question=(
            "Walk through a complex multi-step scenario where you weigh trade-offs, "
            "handle failure modes, and choose between competing approaches under constraints."
        ),
        category="technical",
        question_type="scenario",
        skill_tag="Planning",
    )
    depth = classify_study_material_depth(scenario_q, {"title": "Mystery Role"})
    assert depth != "simple_factual"
    assert depth in {"complex_scenario", "advanced_multi_step", "practical_workflow"}


def test_hr_motivation_with_compliance_words_stays_behavioral() -> None:
    """§9 Problem A: a motivation/fit question must NOT be over-classified as a
    complex scenario merely because it mentions standards/protocol/compliance."""
    q = _q(
        question=(
            "Why do you want to work as a Clinical Pharmacist here, and how do you "
            "approach clinical governance, protocol and safety standards?"
        ),
        category="hr",
        question_type="motivation",
        skill_tag="Motivation",
    )
    assert classify_study_material_depth(q, {"title": "Clinical Pharmacist"}) == "hr_behavioral"


def test_role_specific_excites_with_load_calc_context_stays_hr_behavioral() -> None:
    """E2.3 pass 2: technical role context must not force standard_technical depth."""
    job = {
        "title": "Electrical Engineer",
        "responsibilities": ["Load calculations"],
        "requirements": ["Cable Sizing", "Load Calculations"],
        "extracted_skills": [{"skill": "Cable Sizing"}, {"skill": "Load Calculations"}],
    }
    q = _q(
        question=(
            "What excites you specifically about this Electrical Engineer position, "
            "based on what you've read? In this role-specific case, address: "
            "Electrical Engineer context: Load calculations."
        ),
        category="role_specific",
        skill_tag=None,
    )
    assert classify_study_material_depth(q, job) == "hr_behavioral"


def test_thin_behavioral_keeps_behavioral_depth() -> None:
    """§9 Problem B: thin input alters conservatism, not question meaning — a
    behavioral prompt must not be rewritten into simple_factual."""
    thin_job = {"title": "Mystery Role"}
    q = _q(
        question="Tell me about a time you handled a difficult situation.",
        category="behavioral",
        question_type="behavioral",
        skill_tag="Teamwork",
    )
    assert classify_study_material_depth(q, thin_job) == "hr_behavioral"
    # Thin input must not collapse behavioral semantics into simple/standard.
    resolved = resolve_study_material_budget(q, thin_job)
    assert resolved.study_depth == "hr_behavioral"


def test_true_complex_safety_scenario_still_complex() -> None:
    """§9 negative control: a genuine multi-constraint safety/regulatory scenario
    must still classify as complex, not be flattened by the motivation guard."""
    q = _q(
        question=(
            "Walk through a complex multi-constraint safety scenario where regulatory "
            "limits, patient risk, and staffing all conflict and you must decide."
        ),
        category="technical",
        question_type="scenario",
        skill_tag="Medication Review",
    )
    depth = classify_study_material_depth(q, {"title": "Clinical Pharmacist"})
    assert depth in {"complex_scenario", "advanced_multi_step"}


def test_budget_status_consistent_with_word_count() -> None:
    """Invariant: a module whose actual words exceed its reported target max must
    NOT be labelled within_target (no internally contradictory metadata)."""
    for title, focus in (
        ("Data Analyst", ["SQL"]),
        ("Senior Systems Engineer", ["System Design"]),
        ("Clinical Pharmacist", ["Medication Review"]),
    ):
        job = _job(title=title)
        for q in mock_generate_questions(job, focus_areas=focus, difficulty="mid"):
            study = q.get("study_material") or {}
            if not study:
                continue
            actual = int(study.get("actual_word_count") or 0)
            target_max = int(study.get("target_max_words") or 0)
            if target_max and actual > target_max:
                assert study.get("budget_status") != "within_target", (title, study.get("budget_status"), actual, target_max)


def test_model_knowledge_disabled_by_default() -> None:
    assert settings.job_search_enable_model_knowledge is False


def test_answer_limit_separate_from_study_material() -> None:
    job = _job(title="Senior Systems Engineer")
    questions = mock_generate_questions(job, focus_areas=["AWS"], difficulty="mid")
    exportable = [q for q in questions if q.get("model_answer") and not q.get("export_blocked")]
    assert exportable
    for q in exportable:
        answer_words = len((q.get("model_answer") or "").split())
        study = q.get("study_material") or {}
        assert answer_words <= ABSOLUTE_MAX_WORDS
        assert int(study.get("actual_word_count") or 0) <= int(study.get("hard_max_words") or 0)


def test_no_blocked_phrases_or_label_leaks_in_study() -> None:
    job = _job()
    questions = mock_generate_questions(job, focus_areas=["SQL"], difficulty="mid")
    blob = " ".join(
        str(v)
        for q in questions
        for v in (q.get("study_material") or {}).values()
        if isinstance(v, str)
    )
    assert export_blocked_phrase_count(blob) == 0
    assert not re.search(r"\bRole Specific\b", blob)


def test_apply_finalized_module_includes_budget_metadata() -> None:
    q = _q()
    apply_finalized_study_module(q, _job())
    study = q["study_material"]
    assert study.get("study_depth")
    assert study.get("actual_word_count") is not None
    assert study.get("budget_status")
    assert study.get("depth_contract_coverage") is not None


def test_count_words_accuracy() -> None:
    assert count_words("one two three") == 3


def test_thin_conservative_input_detection() -> None:
    job = {"title": "Unknown Role"}
    q = _q()
    signals = collect_complexity_signals(q, job)
    assert is_thin_conservative_input(signals)
