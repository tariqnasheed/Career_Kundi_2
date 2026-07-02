from __future__ import annotations

from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.answer_length_policy import (
    ABSOLUTE_MAX_WORDS,
    WARN_SHORT_WORDS,
    audit_answer_length,
    collect_length_metrics,
)
from app.agents.job_search.tests.regression_metrics import load_golden_cases


def _job_for_case(case: dict) -> dict:
    return {
        "title": case["role"],
        "responsibilities": [f"Deliver {case['skill']} work safely and accurately"],
        "requirements": [case["skill"]],
        "extracted_skills": [{"skill": case["skill"]}],
    }


def test_flexible_answer_length_monitoring() -> None:
    records: list[dict] = []
    for case in load_golden_cases():
        job = _job_for_case(case)
        questions = mock_generate_questions(job, focus_areas=[case["skill"]], difficulty="medium")
        for question in questions:
            if question.get("export_blocked"):
                continue
            answer = (question.get("model_answer") or "").strip()
            if not answer:
                continue
            length_audit = audit_answer_length(answer, question)
            records.append(
                {
                    "role": case["role"],
                    "question": question.get("question") or "",
                    "word_count": length_audit["word_count"],
                    "intent_aligned": length_audit["passed"],
                }
            )
            assert length_audit["word_count"] <= ABSOLUTE_MAX_WORDS, (
                f'{case["role"]}: answer for "{(question.get("question") or "")[:90]}" '
                f"exceeds {ABSOLUTE_MAX_WORDS} words (actual {length_audit['word_count']})"
            )

    metrics = collect_length_metrics(records)
    print(
        "Flexible answer-length report:",
        f"max={metrics['max_answer_length']}",
        f"over_500={metrics['answers_over_500_count']}",
        f"under_150={metrics['answers_below_150_count']}",
    )
    assert metrics["answers_over_500_count"] == 0
    for short in metrics["under_150_records"]:
        aligned = short.get("intent_aligned")
        assert aligned is True, f"Short answer misaligned: {short}"

    assert WARN_SHORT_WORDS == 150
