from __future__ import annotations

import re
from typing import Any

from app.agents.job_search.knowledge.core_technical_content import (
    get_calculation_pack,
    get_principles_pack,
    get_terminology_pack,
)
from app.agents.job_search.knowledge.domains import classify_skill_domain
from app.agents.job_search.knowledge.normalize import title_case_skill
from app.agents.job_search.quality.domain_density_audit import domain_density_score as _domain_density_score
from app.agents.job_search.quality.key_term_quality_audit import is_valid_key_term


_GENERIC_PATTERNS = (
    "analyze the problem",
    "communicate with the team",
    "ensure compliance",
    "best practices",
    "as needed",
    "where applicable",
)


def _safe_slug(text: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", (text or "").strip().lower())).strip("_")


def build_role_intelligence(job: dict[str, Any]) -> dict[str, Any]:
    role = job.get("title") or "Professional"
    responsibilities = job.get("responsibilities") or []
    reqs = job.get("requirements") or []
    seniority = "Junior to Mid-Level"
    if any("senior" in str(r).lower() for r in responsibilities + reqs):
        seniority = "Senior"
    elif any("entry" in str(r).lower() or "graduate" in str(r).lower() for r in responsibilities + reqs):
        seniority = "Entry"

    return {
        "role": role,
        "domain": classify_skill_domain(role, role),
        "seniority": seniority,
        "responsibilities": responsibilities[:8],
        "requirements": reqs[:8],
        "stream_id": job.get("stream_id"),
        "company_name": job.get("company_name"),
    }


def build_skill_card(skill: str, job: dict[str, Any]) -> dict[str, Any]:
    role = job.get("title") or "Professional"
    resp = (job.get("responsibilities") or [None])[0]
    if isinstance(resp, dict):
        resp = resp.get("text")
    responsibility = str(resp or "core duties")
    domain = classify_skill_domain(skill, role)
    terms_pack = get_terminology_pack(skill, role, responsibility)
    principles_pack = get_principles_pack(skill, role, responsibility)
    calc_pack = get_calculation_pack(skill, role, responsibility)

    terms = terms_pack.get("terms", [])[:6]
    core_terms = [t.get("term", "") for t in terms if isinstance(t, dict) and t.get("term")]
    core_terms = [t for t in core_terms if is_valid_key_term(t)]
    principles = principles_pack.get("principles", [])[:5]
    operating_steps = principles_pack.get("operating_steps", [])[:5]
    formula_or_method: list[str] = []
    if calc_pack:
        formula_or_method = (calc_pack.get("steps") or [])[:4]

    expectation = (
        f"Can apply {title_case_skill(skill)} in {role} work for '{responsibility}', "
        "with standards, quality checks, and measurable outcomes."
    )
    common_mistakes = [
        "Using generic process language without technical specifics.",
        "Skipping standards/protocol checks before sign-off.",
        "Missing the final verification step.",
    ]
    if formula_or_method:
        common_mistakes.append("Ignoring units or threshold limits in quantitative checks.")

    return {
        "skill": title_case_skill(skill),
        "skill_slug": _safe_slug(skill),
        "role_context": f"{role} - {responsibility}",
        "domain": domain,
        "why_employers_ask": (
            f"To verify practical and role-specific command of {title_case_skill(skill)}, not memorized generic wording."
        ),
        "core_concepts": core_terms[:6],
        "formula_or_method": formula_or_method,
        "common_mistakes": common_mistakes,
        "interview_answer_expectation": [
            "Mention the role-specific workflow and checkpoints.",
            "Reference at least one standard/protocol when available.",
            "Include one concrete risk or failure mode and how it is controlled.",
            "Tie the result to quality, safety, or service outcome.",
        ],
        "mini_example": calc_pack.get("answer") if calc_pack else (operating_steps[0] if operating_steps else ""),
        "standards": (terms_pack.get("standards") or principles_pack.get("standards") or [])[:3],
        "operating_steps": operating_steps,
        "source_packs": {
            "terminology": terms_pack,
            "principles": principles_pack,
            "calculation": calc_pack,
        },
        "employer_expectation": expectation,
    }


def build_skill_card_bank(job: dict[str, Any], skills: list[str]) -> dict[str, dict[str, Any]]:
    cards: dict[str, dict[str, Any]] = {}
    for skill in skills:
        if not skill:
            continue
        key = _safe_slug(skill)
        if key not in cards:
            cards[key] = build_skill_card(skill, job)
    return cards


def map_question_to_skill_card(question: dict[str, Any], skill_cards: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    skill = question.get("skill_tag")
    if not skill:
        return None
    return skill_cards.get(_safe_slug(str(skill)))


def generic_phrase_count(text: str) -> int:
    lowered = (text or "").lower()
    return sum(1 for p in _GENERIC_PATTERNS if p in lowered)


def domain_density_score(text: str, card: dict[str, Any] | None) -> float:
    if not text or not card:
        return 0.0
    terms = [str(t) for t in (card.get("core_concepts") or []) if str(t).strip()]
    return _domain_density_score(text, terms)
