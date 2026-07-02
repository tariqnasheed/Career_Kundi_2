from __future__ import annotations

from typing import Any

from app.agents.job_search.quality.broken_template_audit import contains_broken_pattern
from app.agents.job_search.quality.compiler_boilerplate_audit import contains_universal_boilerplate
from app.agents.job_search.quality.domain_contamination_audit import has_domain_contamination
from app.agents.job_search.quality.domain_density_audit import (
    domain_density_breakdown,
    domain_density_from_context,
)
from app.agents.job_search.quality.expert_naturalness_audit import (
    expert_naturalness_failures,
    expert_naturalness_score,
)
from app.agents.job_search.quality.generic_phrase_audit import contains_generic_pattern
from app.agents.job_search.quality.legacy_template_audit import contains_legacy_template
from app.agents.job_search.quality.answer_length_policy import ABSOLUTE_MAX_WORDS
from app.agents.job_search.quality.skill_card_consumption_audit import skill_card_consumption_score


def count_domain_terms(answer: str, required_domain_terms: list[str]) -> int:
    lowered = (answer or "").lower()
    return sum(1 for t in required_domain_terms if t and str(t).lower() in lowered)


def has_real_example(answer: str) -> bool:
    return len(answer.split()) >= 25 and any(
        tok in answer.lower() for tok in ("during", "when", "for example", "case", "incident")
    )


def mentions_standard(answer: str, contract: dict[str, Any], slots: dict[str, Any]) -> bool:
    standards = slots.get("standards_or_regulations", []) or []
    lowered = (answer or "").lower()
    return any(str(s).lower() in lowered for s in standards)


def mentions_common_mistake(answer: str, slots: dict[str, Any]) -> bool:
    lowered = (answer or "").lower()
    mistakes = slots.get("common_mistakes", []) or []
    return any(str(m).lower()[:30] in lowered for m in mistakes if m)


def validate_answer(answer: str, contract: dict[str, Any], slots: dict[str, Any]) -> list[str]:
    failures: list[str] = []

    if len(answer.split()) > ABSOLUTE_MAX_WORDS:
        failures.append("answer_too_long")

    density = domain_density_from_context(answer, contract, slots)
    min_required = max(2, min(contract.get("minimum_domain_terms_required", 1), 4))
    if density < 35 and count_domain_terms(answer, contract.get("required_domain_terms", [])) < min_required:
        failures.append("low_domain_density")

    if contains_generic_pattern(answer):
        failures.append("generic_pattern_detected")

    if contains_broken_pattern(answer):
        failures.append("broken_template_detected")

    if contains_legacy_template(answer):
        failures.append("legacy_template_leaked")
    if contains_universal_boilerplate(answer):
        failures.append("universal_boilerplate_detected")

    if has_domain_contamination(answer, contract.get("role_family", "default")):
        failures.append("domain_contamination_detected")

    failures += expert_naturalness_failures(answer, contract, slots)

    if "example" in answer.lower() and not has_real_example(answer):
        failures.append("empty_or_weak_example")

    if contract.get("must_include_standard") and not mentions_standard(answer, contract, slots):
        failures.append("missing_standard")

    if contract.get("must_include_common_mistake") and not mentions_common_mistake(answer, slots):
        failures.append("missing_common_mistake")

    return failures
