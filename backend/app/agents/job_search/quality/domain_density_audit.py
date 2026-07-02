from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from app.agents.job_search.quality.key_term_quality_audit import is_valid_key_term

GENERIC_DOMAIN_STOP_TERMS = {
    "evidence",
    "process",
    "framework",
    "outcome",
    "quality",
    "operational",
    "reliable",
    "constraints",
    "assumptions",
    "sign-off",
    "verification",
    "professional",
    "standard",
    "workflow",
    "compliance",
}

CORE_WEIGHT = 0.60
STANDARDS_WEIGHT = 0.25
SAFETY_VERIFICATION_WEIGHT = 0.15
CORE_CONTRIBUTION_CAP = 41.0
STANDARDS_COVERAGE_CAP = 70.0
STANDARDS_CONTRIBUTION_CAP = 13.5
SAFETY_VERIFICATION_COVERAGE_CAP = 55.0
SAFETY_VERIFICATION_CONTRIBUTION_CAP = 7.5
CORE_ONLY_FLOOR_MULTIPLIER = 0.78
PHRASE_OVERLAP_THRESHOLD = 0.72

DENSITY_TARGET_MIN = 45.0
DENSITY_TARGET_MAX = 65.0
DENSITY_SOFT_MIN = 42.0
NATURALNESS_SOFT_THRESHOLD = 85.0


def is_valid_domain_term(term: str, *, role: str = "", skill: str = "") -> bool:
    t = (term or "").strip().lower()
    if not t or t in GENERIC_DOMAIN_STOP_TERMS:
        return False
    if role and t == role.strip().lower():
        return False
    if skill and t == skill.strip().lower():
        return False
    if len(t.split()) > 6:
        return False
    return is_valid_key_term(term)


def _normalize_phrase(term: str) -> str:
    return re.sub(r"\s+", " ", (term or "").strip().lower())


def _phrases_overlap(a: str, b: str, threshold: float = PHRASE_OVERLAP_THRESHOLD) -> bool:
    a_n = _normalize_phrase(a)
    b_n = _normalize_phrase(b)
    if not a_n or not b_n:
        return False
    if a_n == b_n or a_n in b_n or b_n in a_n:
        return True
    return SequenceMatcher(None, a_n, b_n).ratio() >= threshold


def _token_overlap_ratio(a: str, b: str) -> float:
    ta = {t for t in _normalize_phrase(a).split() if len(t) > 2}
    tb = {t for t in _normalize_phrase(b).split() if len(t) > 2}
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))


def _dedupe_against_workflow(
    verification_terms: list[str],
    workflow_terms: list[str],
) -> tuple[list[str], int]:
    unique: list[str] = []
    overlap_excluded = 0
    for term in verification_terms:
        if any(
            _phrases_overlap(term, workflow_term) or _token_overlap_ratio(term, workflow_term) >= 0.75
            for workflow_term in workflow_terms
        ):
            overlap_excluded += 1
            continue
        unique.append(term)
    return unique, overlap_excluded


def _categorize_expected_terms(
    contract: dict[str, Any] | None,
    slots: dict[str, Any] | None,
    card: dict[str, Any] | None = None,
    pack: dict[str, Any] | None = None,
) -> dict[str, Any]:
    role = str((contract or {}).get("role") or "")
    skill = str((contract or {}).get("mapped_skill") or "")

    core: list[str] = []
    standards_tools: list[str] = []
    verification: list[str] = []
    workflow: list[str] = []

    if pack:
        core += [str(t) for t in pack.get("domain_terms", [])]
    if contract:
        core += [str(t) for t in (contract.get("required_domain_terms") or [])]
    if card:
        core += [str(t) for t in (card.get("core_concepts") or [])]
    if slots:
        standards_tools += [str(t) for t in (slots.get("standards_or_regulations") or [])]
        verification += [str(t) for t in (slots.get("safety_checks") or [])]
        workflow += [str(t) for t in (slots.get("practical_steps") or [])]
        workflow += [str(t) for t in (slots.get("quality_checks") or [])]

    def _clean(items: list[str]) -> list[str]:
        cleaned = [
            t.strip().lower()
            for t in items
            if is_valid_domain_term(str(t), role=role, skill=skill)
        ]
        return list(dict.fromkeys(cleaned))

    core_clean = _clean(core)
    standards_clean = [s for s in _clean(standards_tools) if s not in set(core_clean)]
    workflow_clean = _clean(workflow)
    verification_raw = _clean(verification)
    verification_clean, overlap_excluded = _dedupe_against_workflow(verification_raw, workflow_clean)

    return {
        "core_domain_terms": core_clean,
        "standards_tools": standards_clean,
        "verification_checks": verification_clean,
        "workflow_steps": workflow_clean,
        "overlap_excluded_count": overlap_excluded,
    }


def collect_expected_domain_terms(
    contract: dict[str, Any] | None,
    slots: dict[str, Any] | None,
    card: dict[str, Any] | None = None,
    pack: dict[str, Any] | None = None,
) -> list[str]:
    cats = _categorize_expected_terms(contract, slots, card=card, pack=pack)
    merged: list[str] = []
    for key in ("core_domain_terms", "standards_tools", "verification_checks"):
        merged.extend(cats.get(key, []))
    return list(dict.fromkeys(merged))


def _coverage(answer: str, terms: list[str]) -> float:
    if not terms:
        return 0.0
    answer_lower = (answer or "").lower()
    hits = {term for term in terms if term in answer_lower}
    return (len(hits) / len(terms)) * 100


def domain_density_breakdown(
    answer: str,
    contract: dict[str, Any] | None = None,
    slots: dict[str, Any] | None = None,
    card: dict[str, Any] | None = None,
    pack: dict[str, Any] | None = None,
) -> dict[str, float]:
    cats = _categorize_expected_terms(contract, slots, card=card, pack=pack)
    core_cov = _coverage(answer, cats["core_domain_terms"])
    std_cov = _coverage(answer, cats["standards_tools"])
    verify_cov = _coverage(answer, cats["verification_checks"])
    workflow_cov = _coverage(answer, cats["workflow_steps"])

    verify_capped = min(verify_cov, SAFETY_VERIFICATION_COVERAGE_CAP)
    core_contribution = min(core_cov * CORE_WEIGHT, CORE_CONTRIBUTION_CAP)
    std_contribution = min(min(std_cov, STANDARDS_COVERAGE_CAP) * STANDARDS_WEIGHT, STANDARDS_CONTRIBUTION_CAP)
    verify_contribution = min(verify_capped * SAFETY_VERIFICATION_WEIGHT, SAFETY_VERIFICATION_CONTRIBUTION_CAP)
    final_score = round(core_contribution + std_contribution + verify_contribution, 1)

    if not cats["standards_tools"] and not cats["verification_checks"] and core_cov >= 50.0:
        final_score = round(max(final_score, min(core_cov * CORE_ONLY_FLOOR_MULTIPLIER, 52.0)), 1)

    return {
        "domain_density_score": final_score,
        "final_recalibrated_density": final_score,
        "core_density": round(core_cov, 1),
        "core_domain_term_coverage": round(core_cov, 1),
        "standards_density": round(std_cov, 1),
        "standard_tool_coverage": round(std_cov, 1),
        "safety_verification_density": round(verify_cov, 1),
        "safety_verification_density_capped": round(verify_capped, 1),
        "workflow_term_coverage": round(workflow_cov, 1),
        "overlap_excluded_count": float(cats.get("overlap_excluded_count", 0)),
    }


def domain_density_score(answer: str, expected_terms: list[str]) -> float:
    answer_lower = (answer or "").lower()
    unique_expected = {
        t.strip().lower()
        for t in expected_terms
        if is_valid_domain_term(t)
    }
    if not unique_expected:
        return 0.0
    hits = {term for term in unique_expected if term in answer_lower}
    return round((len(hits) / len(unique_expected)) * 100, 1)


def domain_density_from_context(
    answer: str,
    contract: dict[str, Any] | None,
    slots: dict[str, Any] | None,
    card: dict[str, Any] | None = None,
    pack: dict[str, Any] | None = None,
) -> float:
    breakdown = domain_density_breakdown(answer, contract, slots, card=card, pack=pack)
    return breakdown["final_recalibrated_density"]


def evaluate_density_band(
    density: float,
    *,
    naturalness: float | None = None,
    naturalness_soft_threshold: float = NATURALNESS_SOFT_THRESHOLD,
) -> dict[str, Any]:
    in_target_band = DENSITY_TARGET_MIN <= density <= DENSITY_TARGET_MAX
    is_low_outlier = density < DENSITY_TARGET_MIN
    is_high_outlier = density > DENSITY_TARGET_MAX
    blocking = False
    reason = ""

    if is_low_outlier:
        if density >= DENSITY_SOFT_MIN and (naturalness or 0.0) >= naturalness_soft_threshold:
            blocking = False
            reason = (
                "small standards bucket / safety-heavy practical role / "
                "expert naturalness remains acceptable"
            )
        else:
            blocking = True
            reason = "density below soft minimum without acceptable naturalness"
    elif is_high_outlier:
        if (naturalness or 0.0) >= naturalness_soft_threshold:
            blocking = False
            reason = "high core/standards coverage with acceptable naturalness"
        else:
            blocking = True
            reason = "density above target band without acceptable naturalness"

    return {
        "in_target_band": in_target_band,
        "is_low_outlier": is_low_outlier,
        "is_high_outlier": is_high_outlier,
        "blocking": blocking,
        "non_blocking": (is_low_outlier or is_high_outlier) and not blocking,
        "status": (
            "in_band"
            if in_target_band
            else ("non_blocking_low_outlier" if is_low_outlier and not blocking else "outlier")
        ),
        "reason": reason,
    }


def role_density_audit_record(
    *,
    role: str,
    skill: str,
    question: str,
    answer: str,
    contract: dict[str, Any] | None,
    slots: dict[str, Any] | None,
    card: dict[str, Any] | None = None,
    pack: dict[str, Any] | None = None,
    naturalness: float | None = None,
) -> dict[str, Any]:
    breakdown = domain_density_breakdown(answer, contract, slots, card=card, pack=pack)
    density = breakdown["final_recalibrated_density"]
    band = evaluate_density_band(density, naturalness=naturalness)
    return {
        "role": role,
        "skill": skill,
        "question": question,
        "final_recalibrated_density": density,
        **band,
        "core_density": breakdown["core_density"],
        "standards_density": breakdown["standards_density"],
        "safety_verification_density": breakdown["safety_verification_density"],
        "overlap_excluded_count": breakdown["overlap_excluded_count"],
    }
