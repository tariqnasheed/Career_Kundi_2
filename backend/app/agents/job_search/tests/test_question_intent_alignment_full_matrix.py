from __future__ import annotations

from collections import defaultdict

from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.question_intent_alignment_audit import audit_question_intent_alignment
from app.agents.job_search.tests.regression_metrics import load_golden_cases

OVERALL_PASS_RATE_FLOOR = 95.0
INTENT_PASS_RATE_FLOOR = 90.0


def _job_for_case(case: dict) -> dict:
    return {
        "title": case["role"],
        "responsibilities": [f"Deliver {case['skill']} work safely and accurately"],
        "requirements": [case["skill"]],
        "extracted_skills": [{"skill": case["skill"]}],
    }


def test_question_intent_alignment_full_matrix() -> None:
    cases = load_golden_cases()
    assert len(cases) >= 15

    total_checked = 0
    total_passed = 0
    failures: list[str] = []
    intent_buckets: dict[str, dict[str, int]] = defaultdict(lambda: {"pass": 0, "fail": 0})

    for case in cases:
        job = _job_for_case(case)
        questions = mock_generate_questions(job, focus_areas=[case["skill"]], difficulty="medium")
        for question in questions:
            if question.get("export_blocked"):
                continue
            answer = (question.get("model_answer") or "").strip()
            if not answer:
                continue

            audit = audit_question_intent_alignment(answer, question)
            intent = audit["intent"]
            total_checked += 1
            if audit["passed"]:
                total_passed += 1
                intent_buckets[intent]["pass"] += 1
            else:
                intent_buckets[intent]["fail"] += 1
                reason = audit["errors"][0] if audit["errors"] else "unknown failure"
                failures.append(
                    f"{case['role']} / intent={intent} / question=\"{question.get('question', '')[:90]}\" / {reason}"
                )

    overall_rate = round((total_passed / total_checked) * 100, 1) if total_checked else 0.0
    intent_rates = {
        intent: round((counts["pass"] / max(counts["pass"] + counts["fail"], 1)) * 100, 1)
        for intent, counts in sorted(intent_buckets.items())
    }

    print(f"Full-matrix intent alignment: {total_passed}/{total_checked} passed ({overall_rate}%)")
    for intent, rate in intent_rates.items():
        print(f"  {intent}: {rate}% ({intent_buckets[intent]['pass']}/{intent_buckets[intent]['pass'] + intent_buckets[intent]['fail']})")
    for failure in failures[:20]:
        print(f"  FAIL: {failure}")

    assert total_checked > 0, "No generated questions were checked"
    assert overall_rate >= OVERALL_PASS_RATE_FLOOR, (
        f"Overall intent-alignment pass rate too low "
        f"(expected >= {OVERALL_PASS_RATE_FLOOR}%, actual {overall_rate}%, checked {total_checked})"
    )
    for intent, rate in intent_rates.items():
        assert rate >= INTENT_PASS_RATE_FLOOR, (
            f"Intent category '{intent}' pass rate too low "
            f"(expected >= {INTENT_PASS_RATE_FLOOR}%, actual {rate}%)"
        )
