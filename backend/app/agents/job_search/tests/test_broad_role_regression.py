from __future__ import annotations

import json
import re
from pathlib import Path

from app.agents.job_search.knowledge.answer_builders import (
    MAX_COMPLIANCE_WORKFLOW_SIMILARITY,
    compliance_workflow_overlap_ratio,
)
from app.agents.job_search.knowledge.content_engine import build_model_answer
from app.agents.job_search.knowledge.evidence_packs import get_evidence_pack
from app.agents.job_search.knowledge.question_contracts import create_question_contract
from app.agents.job_search.knowledge.skill_cards import build_skill_card
from app.agents.job_search.quality.compiler_boilerplate_audit import universal_boilerplate_count
from app.agents.job_search.quality.domain_contamination_audit import domain_contamination_count
from app.agents.job_search.quality.domain_density_audit import domain_density_breakdown
from app.agents.job_search.quality.expert_naturalness_audit import expert_naturalness_score
from app.agents.job_search.quality.final_surface_quality_gate import validate_final_surface

DOMAIN_DENSITY_MIN = 45.0
DOMAIN_DENSITY_SOFT_MIN = 42.0
DOMAIN_DENSITY_MAX = 65.0
EXPERT_NATURALNESS_AVG_MIN = 85.0


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
    return answer, {"question": question, "contract": contract, "job": job}


def test_golden_final_surface_quality() -> None:
    cases = _golden_cases()
    assert len(cases) >= 15
    passed = 0
    for case in cases:
        answer, ctx = _generate_answer(case)
        question = ctx["question"]
        contract = ctx["contract"]
        assert answer, f"{case['role']} produced empty/blocked answer"
        assert question.get("answer_source") == "contract_compiler"
        assert question.get("used_fallback_template") is False
        assert question.get("used_legacy_polisher") is False

        failures = validate_final_surface(answer, question, contract)
        assert not failures, f"{case['role']} failed final surface gate: {failures}"
        naturalness = expert_naturalness_score(answer, contract, question.get("evidence_slots"))
        assert naturalness >= 70, f"{case['role']} low expert naturalness: {naturalness}"
        assert "My practical workflow is:" not in answer
        assert "Key terms are" not in answer
        assert "I would verify the work by" not in answer
        assert answer.strip().endswith((".", "!", "?"))
        assert answer.count("\n\n") >= 2
        assert universal_boilerplate_count(answer) == 0
        assert domain_contamination_count(answer, case["role_family"]) == 0
        low = answer.lower()
        for term in case["must_contain"]:
            assert term.lower() in low, f"{case['role']} missing required term: {term}"
        for term in case["must_not_contain"]:
            assert term.lower() not in low, f"{case['role']} contains forbidden term: {term}"
        passed += 1
    assert passed == len(cases)


_BOILERPLATE_PATTERNS = [
    r"In this .* context",
    r"The critical discipline is evidence",
    r"When conditions change",
    r"stays reliable under real operational constraints",
    r"documented the control points",
    r"structured verification",
    r"clarify required outcome, constraints, and stakeholders",
    r"apply .* using documented procedures",
]


def test_broad_role_regression_no_universal_boilerplate() -> None:
    cases = _golden_cases()
    assert len(cases) >= 15
    naturalness_scores: list[float] = []
    density_outliers: list[str] = []

    for case in cases:
        answer, ctx = _generate_answer(case)
        question = ctx["question"]
        contract = ctx["contract"]
        slots = question.get("evidence_slots") or {}
        assert answer, f"{case['role']} blocked export"
        for pattern in _BOILERPLATE_PATTERNS:
            assert not re.search(pattern, answer, re.I), f"{case['role']} matched boilerplate: {pattern}"
        failures = validate_final_surface(answer, question, contract)
        assert not failures, f"{case['role']} surface failures: {failures}"
        consumption = (question.get("quality_audit") or {}).get("skill_card_consumption_score", 0)
        assert consumption >= 50, f"{case['role']} low skill-card consumption: {consumption}"
        naturalness = expert_naturalness_score(answer, contract, slots)
        naturalness_scores.append(naturalness)
        assert naturalness >= 70, f"{case['role']} low expert naturalness: {naturalness}"
        assert "My practical workflow is:" not in answer
        assert "For compliance, I check" not in answer
        assert "Key terms are" not in answer
        assert "I also apply safety checks such as" not in answer
        assert "applies domain methods, standards, and verification controls" not in answer
        assert "I would verify the work by" not in answer

        overlap = compliance_workflow_overlap_ratio(answer)
        assert overlap <= MAX_COMPLIANCE_WORKFLOW_SIMILARITY, (
            f"{case['role']} compliance/workflow overlap too high: {overlap:.2f}"
        )

        pack = get_evidence_pack(case["role_family"])
        density = domain_density_breakdown(
            answer, contract, slots, card=question.get("skill_card"), pack=pack
        )["final_recalibrated_density"]
        if density < DOMAIN_DENSITY_MIN:
            if density >= DOMAIN_DENSITY_SOFT_MIN and naturalness >= EXPERT_NATURALNESS_AVG_MIN:
                density_outliers.append(f"{case['role']}:{density}% (low)")
            else:
                raise AssertionError(f"{case['role']} domain density below band: {density}%")
        if density > DOMAIN_DENSITY_MAX:
            if naturalness >= EXPERT_NATURALNESS_AVG_MIN:
                density_outliers.append(f"{case['role']}:{density}% (high)")
            else:
                raise AssertionError(f"{case['role']} domain density above band: {density}%")

    avg_naturalness = sum(naturalness_scores) / len(naturalness_scores)
    assert avg_naturalness >= EXPERT_NATURALNESS_AVG_MIN, (
        f"expert naturalness average below {EXPERT_NATURALNESS_AVG_MIN}: {avg_naturalness}"
    )
