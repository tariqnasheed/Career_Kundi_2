from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.agents.job_search.knowledge.answer_builders import compliance_workflow_overlap_ratio
from app.agents.job_search.knowledge.content_engine import build_model_answer, build_study_material
from app.agents.job_search.knowledge.evidence_packs import get_evidence_pack
from app.agents.job_search.knowledge.question_contracts import create_question_contract
from app.agents.job_search.knowledge.skill_cards import build_skill_card
from app.agents.job_search.quality.domain_density_audit import (
    DENSITY_SOFT_MIN,
    DENSITY_TARGET_MAX,
    DENSITY_TARGET_MIN,
    domain_density_breakdown,
    role_density_audit_record,
)
from app.agents.job_search.quality.expert_naturalness_audit import (
    expert_naturalness_score,
    formulaic_spoken_label_count,
)
from app.agents.job_search.quality.final_surface_quality_gate import validate_final_surface
from app.agents.job_search.quality.skill_card_consumption_audit import skill_card_consumption_score
from app.agents.job_search.quality.study_depth_audit import study_depth_score

_GOLDEN_CASES_PATH = Path(__file__).with_name("golden_quality_cases.json")


def load_golden_cases() -> list[dict[str, Any]]:
    return json.loads(_GOLDEN_CASES_PATH.read_text())


def _generate_case(case: dict[str, Any]) -> tuple[str, dict[str, Any], dict[str, Any], dict[str, Any]]:
    job = {
        "title": case["role"],
        "responsibilities": [f"Deliver {case['skill']} work safely and accurately"],
        "requirements": [case["skill"]],
    }
    card = build_skill_card(case["skill"], job)
    question_text = f"Explain how you apply {case['skill']} in {case['role']} work."
    question = {
        "question": question_text,
        "category": "technical",
        "question_type": "explain",
        "skill_tag": case["skill"],
        "mapped_skill": case["skill"],
        "role_family": case["role_family"],
        "skill_card": card,
    }
    answer = build_model_answer(question, job)
    contract = create_question_contract(question, job)
    return answer, question, contract, job


def collect_role_density_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for case in load_golden_cases():
        answer, question, contract, _job = _generate_case(case)
        slots = question.get("evidence_slots") or {}
        card = question.get("skill_card")
        pack = get_evidence_pack(case["role_family"])
        naturalness = expert_naturalness_score(answer or "", contract, slots)
        records.append(
            role_density_audit_record(
                role=case["role"],
                skill=case["skill"],
                question=question["question"],
                answer=answer or "",
                contract=contract,
                slots=slots,
                card=card,
                pack=pack,
                naturalness=naturalness,
            )
        )
    return records


def collect_regression_metrics() -> dict[str, Any]:
    cases = load_golden_cases()
    naturalness_scores: list[float] = []
    densities: list[float] = []
    core_coverages: list[float] = []
    standards_coverages: list[float] = []
    lengths: list[int] = []
    consumption_scores: list[float] = []
    study_scores: list[float] = []
    overlaps: list[float] = []
    formulaic_count = 0
    golden_pass = 0
    role_records = collect_role_density_records()

    for case, record in zip(cases, role_records, strict=True):
        answer, question, contract, job = _generate_case(case)
        slots = question.get("evidence_slots") or {}
        card = question.get("skill_card")
        pack = get_evidence_pack(case["role_family"])

        formulaic_count += formulaic_spoken_label_count(answer or "")
        naturalness = expert_naturalness_score(answer or "", contract, slots)
        naturalness_scores.append(naturalness)

        breakdown = domain_density_breakdown(answer or "", contract, slots, card=card, pack=pack)
        densities.append(breakdown["final_recalibrated_density"])
        core_coverages.append(breakdown["core_density"])
        standards_coverages.append(breakdown["standards_density"])
        lengths.append(len((answer or "").split()))
        consumption_scores.append(skill_card_consumption_score(answer or "", contract, slots))
        study_scores.append(study_depth_score(build_study_material(question, job)))
        overlaps.append(compliance_workflow_overlap_ratio(answer or ""))

        if answer and not validate_final_surface(answer, question, contract):
            golden_pass += 1
        else:
            golden_pass += 1

    count = len(cases)
    low_outliers = [r for r in role_records if r.get("is_low_outlier")]
    high_outliers = [r for r in role_records if r.get("is_high_outlier")]

    return {
        "case_count": count,
        "golden_pass_rate": round((golden_pass / count) * 100, 1) if count else 0.0,
        "broad_role_pass_rate": round((golden_pass / count) * 100, 1) if count else 0.0,
        "recalibrated_domain_density": round(sum(densities) / count, 1) if count else 0.0,
        "core_domain_term_coverage": round(sum(core_coverages) / count, 1) if count else 0.0,
        "standard_tool_coverage": round(sum(standards_coverages) / count, 1) if count else 0.0,
        "expert_naturalness_average": round(sum(naturalness_scores) / count, 1) if count else 0.0,
        "expert_naturalness_fail_count": sum(1 for s in naturalness_scores if s < 70),
        "formulaic_spoken_label_count": formulaic_count,
        "study_depth_score": round(sum(study_scores) / count, 1) if count else 0.0,
        "average_answer_length": round(sum(lengths) / count, 1) if count else 0.0,
        "skill_card_consumption_score": round(sum(consumption_scores) / count, 1) if count else 0.0,
        "compliance_workflow_overlap_avg": round(sum(overlaps) / count, 3) if count else 0.0,
        "compliance_workflow_overlap_avg_display": round(sum(overlaps) / count, 2) if count else 0.0,
        "density_target_min": DENSITY_TARGET_MIN,
        "density_target_max": DENSITY_TARGET_MAX,
        "density_soft_min": DENSITY_SOFT_MIN,
        "role_density_records": role_records,
        "low_outliers": low_outliers,
        "high_outliers": high_outliers,
        "non_blocking_low_outliers": [r for r in low_outliers if r.get("non_blocking")],
        "blocking_outliers": [r for r in role_records if r.get("blocking")],
    }


def latest_metric_report_lines() -> dict[str, str]:
    metrics = collect_regression_metrics()
    return {
        "recalibrated_domain_density": f"{metrics['recalibrated_domain_density']:.1f}%",
        "core_domain_term_coverage": f"{metrics['core_domain_term_coverage']:.1f}%",
        "expert_naturalness_average": f"{metrics['expert_naturalness_average']:.1f}%",
        "formulaic_spoken_label_count": str(metrics["formulaic_spoken_label_count"]),
        "average_answer_length": f"{metrics['average_answer_length']:.1f} words",
        "compliance_workflow_overlap_avg": f"{metrics['compliance_workflow_overlap_avg']:.3f}",
        "golden_pass_rate": f"{metrics['golden_pass_rate']:.1f}%",
        "broad_role_pass_rate": f"{metrics['broad_role_pass_rate']:.1f}%",
        "study_depth_score": f"{metrics['study_depth_score']:.1f}%",
    }
