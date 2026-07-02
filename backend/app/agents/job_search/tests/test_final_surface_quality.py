from __future__ import annotations

import json
from pathlib import Path

from app.agents.job_search.knowledge.content_engine import build_model_answer
from app.agents.job_search.knowledge.question_contracts import create_question_contract
from app.agents.job_search.knowledge.skill_cards import build_skill_card
from app.agents.job_search.quality.compiler_boilerplate_audit import universal_boilerplate_count
from app.agents.job_search.quality.domain_contamination_audit import domain_contamination_count
from app.agents.job_search.quality.final_surface_quality_gate import validate_final_surface


def _golden_cases() -> list[dict]:
    path = Path(__file__).with_name("golden_quality_cases.json")
    return json.loads(path.read_text())


def _generate_answer(case: dict) -> tuple[str, dict]:
    job = {
        "title": case["role"],
        "responsibilities": [f"Deliver {case['skill']} work safely and accurately"],
        "requirements": [case["skill"]],
    }
    card = build_skill_card(case["skill"], job)
    question = {
        "question": f"Explain how you apply {case['skill']} in {case['role']} work.",
        "category": "technical",
        "question_type": "explain",
        "skill_tag": case["skill"],
        "mapped_skill": case["skill"],
        "role_family": case["role_family"],
        "skill_card": card,
    }
    answer = build_model_answer(question, job)
    contract = create_question_contract(question, job)
    return answer, {"question": question, "contract": contract}


def test_golden_final_surface_quality() -> None:
    cases = _golden_cases()
    assert len(cases) >= 15
    for case in cases:
        answer, ctx = _generate_answer(case)
        question = ctx["question"]
        contract = ctx["contract"]
        assert answer, f"{case['role']} produced empty/blocked answer"

        failures = validate_final_surface(answer, question, contract)
        assert not failures, f"{case['role']} failed final surface gate: {failures}"
        assert answer.strip().endswith((".", "!", "?"))
        assert answer.count("\n\n") >= 2
        assert universal_boilerplate_count(answer) == 0
        assert domain_contamination_count(answer, case["role_family"]) == 0
        low = answer.lower()
        for term in case["must_contain"]:
            assert term.lower() in low, f"{case['role']} missing required term: {term}"
        for term in case["must_not_contain"]:
            assert term.lower() not in low, f"{case['role']} contains forbidden term: {term}"
