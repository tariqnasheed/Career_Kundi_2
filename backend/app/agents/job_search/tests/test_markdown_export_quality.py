from __future__ import annotations

from app.agents.job_search.quality.export_quality_audit import (
    EXPORT_SCORE_FLOOR,
    audit_export_markdown,
    prepare_interview_pack_export,
)
from app.agents.job_search.tests.regression_metrics import load_golden_cases

MIN_EXPORT_QUESTIONS = 3
MIN_EXPORT_ANSWERS = 3
MIN_EXPORT_STUDY_MODULES = 3


def _job_for_case(case: dict) -> dict:
    return {
        "title": case["role"],
        "responsibilities": [f"Deliver {case['skill']} work safely and accurately"],
        "requirements": [case["skill"]],
        "extracted_skills": [{"skill": case["skill"]}],
    }


def test_markdown_export_quality_all_golden_roles() -> None:
    cases = load_golden_cases()
    assert len(cases) >= 15

    audits: list[dict] = []
    for case in cases:
        job = _job_for_case(case)
        markdown, questions, role_overview = prepare_interview_pack_export(
            job,
            focus_skill=case["skill"],
            difficulty="medium",
        )
        audit = audit_export_markdown(
            markdown,
            role=case["role"],
            questions=questions,
            role_overview=role_overview,
        )
        audits.append(audit)

        assert audit["passed"], (
            f"{case['role']} Markdown export failed quality audit "
            f"(score={audit['score']}): {audit['errors']}"
        )
        assert audit["question_count"] >= MIN_EXPORT_QUESTIONS, (
            f"{case['role']} / questions: too few question sections "
            f"(expected >= {MIN_EXPORT_QUESTIONS}, actual {audit['question_count']})"
        )
        assert audit["answer_count"] >= MIN_EXPORT_ANSWERS, (
            f"{case['role']} / model answers: too few answers "
            f"(expected >= {MIN_EXPORT_ANSWERS}, actual {audit['answer_count']})"
        )
        assert audit["study_module_count"] >= MIN_EXPORT_STUDY_MODULES, (
            f"{case['role']} / study modules: too few question-specific study modules "
            f"(expected >= {MIN_EXPORT_STUDY_MODULES}, actual {audit['study_module_count']})"
        )
        assert audit["generic_phrase_count"] == 0, (
            f"{case['role']} / generic phrases: banned phrases found "
            f"(expected 0, actual {audit['generic_phrase_count']})"
        )
        assert audit["empty_section_count"] == 0, (
            f"{case['role']} / headings: empty headings found "
            f"(expected 0, actual {audit['empty_section_count']})"
        )

        if case["role"] == "Barista":
            assert audit["passed"], "Barista remains acceptable despite density outlier"

    average_score = round(sum(a["score"] for a in audits) / len(audits), 1)
    assert average_score >= EXPORT_SCORE_FLOOR, (
        f"Average Markdown export quality score too low "
        f"(expected >= {EXPORT_SCORE_FLOOR}, actual {average_score})"
    )
