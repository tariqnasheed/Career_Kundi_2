from __future__ import annotations

from app.agents.job_search.knowledge.answer_builders import (
    MAX_COMPLIANCE_WORKFLOW_SIMILARITY,
    compliance_workflow_overlap_ratio,
)
from app.agents.job_search.knowledge.skill_cards import build_role_intelligence, build_skill_card
from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.broken_template_audit import contains_broken_pattern
from app.agents.job_search.quality.compiler_boilerplate_audit import contains_universal_boilerplate
from app.agents.job_search.quality.generic_phrase_audit import contains_generic_pattern
from app.agents.job_search.tests.regression_metrics import load_golden_cases

_BANNED_SPOKEN_LABELS = (
    "Key terms are",
    "My practical workflow is:",
    "For compliance, I check",
)


def _job_for_case(case: dict) -> dict:
    return {
        "title": case["role"],
        "responsibilities": [f"Deliver {case['skill']} work safely and accurately"],
        "requirements": [case["skill"]],
        "extracted_skills": [{"skill": case["skill"]}],
    }


def _study_is_question_specific(question: dict, study: dict) -> bool:
    skill = (question.get("mapped_skill") or question.get("skill_tag") or "").lower()
    question_text = (question.get("question") or "").lower()
    blob = " ".join(
        str(study.get(key, ""))
        for key in (
            "what_this_question_tests",
            "overview",
            "beginner_explanation",
            "mini_practice_task",
            "worked_example",
        )
    ).lower()
    if skill and skill in blob:
        return True
    tokens = [t for t in question_text.split() if len(t) > 4]
    return any(token in blob for token in tokens[:6])


def test_interview_pack_export_readiness() -> None:
    cases = load_golden_cases()
    assert len(cases) >= 15

    for case in cases:
        job = _job_for_case(case)
        role_intel = build_role_intelligence(job)
        assert role_intel.get("role") == case["role"]
        assert role_intel.get("responsibilities"), f"{case['role']} missing role introduction responsibilities"

        questions = mock_generate_questions(job, focus_areas=[case["skill"]], difficulty="medium")
        assert questions, f"{case['role']} produced no exportable questions"

        technical_questions = [q for q in questions if q.get("category") in ("technical", "role_specific")]
        assert technical_questions, f"{case['role']} missing technical questions"

        compiler_technical = [
            q
            for q in questions
            if q.get("category") == "technical"
            and q.get("answer_source") == "contract_compiler"
            and q.get("skill_card")
        ]
        assert compiler_technical, f"{case['role']} missing compiler technical questions"

        for question in compiler_technical:
            answer = question.get("model_answer") or ""
            study = question.get("study_material") or {}

            assert answer, f"{case['role']} compiler question missing model answer"
            assert not question.get("export_blocked"), f"{case['role']} export blocked unexpectedly"
            assert "Key terms are" not in answer

            overlap = compliance_workflow_overlap_ratio(answer)
            assert overlap <= MAX_COMPLIANCE_WORKFLOW_SIMILARITY, (
                f"{case['role']} compliance/workflow overlap too high: {overlap:.2f}"
            )
            assert not contains_generic_pattern(answer), f"{case['role']} generic phrase in answer"
            assert not contains_broken_pattern(answer), f"{case['role']} broken template in answer"
            assert not contains_universal_boilerplate(answer), f"{case['role']} universal boilerplate in answer"
            for label in _BANNED_SPOKEN_LABELS:
                assert label not in answer, f"{case['role']} banned spoken label: {label}"

            assert question.get("skill_card"), f"{case['role']} compiler question missing skill card"
            assert question["skill_card"].get("employer_expectation") or question.get("employer_expectation"), (
                f"{case['role']} missing employer expectation on compiler question"
            )
            assert study, f"{case['role']} missing study material for compiler question"
            assert _study_is_question_specific(question, study), (
                f"{case['role']} study material not question-specific for: {question.get('skill_tag')}"
            )

        for question in questions:
            if question.get("skill_card") and question.get("category") == "technical":
                assert question["skill_card"].get("employer_expectation") or question.get("employer_expectation")

        card = build_skill_card(case["skill"], job)
        assert card.get("core_concepts"), f"{case['role']} skill map/core concepts missing"
