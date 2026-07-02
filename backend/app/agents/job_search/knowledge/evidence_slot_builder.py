from __future__ import annotations

from typing import Any

from app.agents.job_search.knowledge.answer_builders import pick_intent_closing
from app.agents.job_search.knowledge.core_technical_content import (
    get_calculation_pack,
    get_principles_pack,
    get_terminology_pack,
)
from app.agents.job_search.knowledge.question_intent import detect_question_intent
from app.agents.job_search.knowledge.evidence_packs import (
    get_evidence_pack,
    resolve_role_family,
    select_role_family_opening,
)
from app.agents.job_search.knowledge.expert_content_library import resolve_expert_content
from app.agents.job_search.knowledge.normalize import title_case_skill
from app.agents.job_search.quality.broken_template_audit import contains_broken_pattern
from app.agents.job_search.quality.compiler_boilerplate_audit import contains_universal_boilerplate
from app.agents.job_search.quality.example_quality_audit import has_weak_example
from app.agents.job_search.quality.generic_phrase_audit import contains_generic_pattern
from app.agents.job_search.quality.key_term_quality_audit import is_valid_key_term


def _sanitize_steps(steps: list[str]) -> list[str]:
    cleaned: list[str] = []
    for step in steps:
        text = str(step).strip()
        if not text or contains_universal_boilerplate(text):
            continue
        cleaned.append(text)
    return cleaned


def _workflow_steps(family_pack: dict[str, Any], skill: str, role: str) -> list[str]:
    checks = family_pack.get("verification_checks") or []
    if checks:
        return [str(c).rstrip(".") for c in checks[:6]]
    return [
        f"Confirm scope and requirements for {title_case_skill(skill)} in {role}",
        f"Execute the {title_case_skill(skill)} workflow with intermediate checks",
        f"Verify outputs against applicable standards and records",
        f"Document decisions, risks, and handover notes",
        f"Review results and update the process for the next cycle",
    ]


def _pick_example(role: str, skill: str, family_pack: dict[str, Any], exp: dict[str, Any]) -> str:
    examples = family_pack.get("role_specific_examples") or []
    if examples:
        return str(examples[0])
    complex_answer = str(exp.get("complex_answer") or "")
    if complex_answer and not has_weak_example(complex_answer) and len(complex_answer.split()) >= 25:
        return complex_answer
    domain = ", ".join((family_pack.get("domain_terms") or [])[:4])
    return (
        f"During a live {role} assignment, I applied {title_case_skill(skill)} using {domain}, "
        f"completed the required verification checks, and recorded measurable outcomes before sign-off."
    )


def _sanitize_text_items(items: list[str]) -> list[str]:
    cleaned: list[str] = []
    for item in items:
        text = str(item).strip()
        if not text:
            continue
        if contains_broken_pattern(text) or contains_universal_boilerplate(text) or contains_generic_pattern(text):
            continue
        cleaned.append(text)
    return cleaned


def _principles_for_question(
    principles_pack: dict[str, Any],
    family_pack: dict[str, Any],
    skill: str,
) -> list[str]:
    principles = _sanitize_text_items(list(principles_pack.get("principles") or []))
    if len(principles) >= 3:
        return principles[:6]
    domain = family_pack.get("domain_terms") or []
    fallback = [
        f"Keep {title_case_skill(skill)} deliverables accurate, coordinated, and revision-controlled",
        f"Verify {title_case_skill(skill)} outputs against applicable standards before issue",
        "Record design decisions, constraints, and compliance evidence for audit and handover",
    ]
    if domain:
        fallback.insert(0, f"Apply {domain[0]} controls consistently in every {title_case_skill(skill)} deliverable")
    return fallback[:6]


def _sanitize_terminology_terms(terms: list[dict[str, Any]]) -> list[dict[str, str]]:
    cleaned: list[dict[str, str]] = []
    for term in terms:
        if not isinstance(term, dict):
            continue
        name = str(term.get("term") or "").strip()
        definition = str(term.get("definition") or "").strip().rstrip(".")
        if not name or not definition:
            continue
        if not is_valid_key_term(name):
            continue
        if contains_broken_pattern(name) or contains_broken_pattern(definition):
            continue
        if contains_universal_boilerplate(name) or contains_universal_boilerplate(definition):
            continue
        cleaned.append({"term": name, "definition": definition})
    return cleaned


def _terminology_terms_for_question(
    q: dict[str, Any],
    terms_pack: dict[str, Any],
    card: dict[str, Any],
    family_pack: dict[str, Any],
    skill: str,
) -> list[dict[str, str]]:
    raw = list(q.get("terminology_terms") or terms_pack.get("terms") or [])
    sanitized = _sanitize_terminology_terms(raw)
    if len(sanitized) >= 4:
        return sanitized[:8]
    fallback_terms: list[dict[str, str]] = []
    for concept in (card.get("core_concepts") or [])[:6]:
        text = str(concept).strip()
        if text and is_valid_key_term(text):
            fallback_terms.append(
                {"term": text, "definition": f"Core {title_case_skill(skill)} control used in professional practice."}
            )
    for term in (family_pack.get("domain_terms") or [])[:6]:
        text = str(term).strip()
        if text and is_valid_key_term(text):
            fallback_terms.append(
                {"term": text, "definition": f"Domain term for {title_case_skill(skill)} work that must be applied correctly."}
            )
    merged = _sanitize_terminology_terms(sanitized + fallback_terms)
    deduped: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in merged:
        key = item["term"].lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped[:8]


def _pick_closing(role_family: str, family_pack: dict[str, Any], role: str, skill: str) -> str:
    closings = family_pack.get("interview_closings") or []
    if closings:
        return str(closings[0])
    legacy = {
        "healthcare": "In an interview, I would show that I can connect pharmacology knowledge to safe prescribing, patient monitoring, escalation, and documentation.",
        "hospitality": "In an interview, I would show that I can prepare drinks consistently while controlling hygiene, allergens, speed, and customer experience.",
        "electrical": "In an interview, I would show that I understand installation as both a practical wiring task and a regulated inspection-and-testing responsibility.",
        "public_administration": "In an interview, I would show that I can run compliant public-service workflows with audit-ready records and clear escalation decisions.",
        "architecture": "In an interview, I would show that I can translate design intent into accurate, compliant, and revision-controlled deliverables.",
    }
    return legacy.get(role_family, f"In an interview, I would show applied technical judgement for {title_case_skill(skill)} in {role}.")


def build_evidence_slots(contract: dict[str, Any], q: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]:
    skill = contract.get("mapped_skill") or q.get("skill_tag") or "General"
    role = contract.get("role") or (job.get("title") or "Professional")
    role_family = resolve_role_family(role, contract.get("role_family") or q.get("role_family"))
    card = q.get("skill_card") or {}
    resp = (job.get("responsibilities") or [None])[0]
    if isinstance(resp, dict):
        resp = resp.get("text")
    exp = resolve_expert_content(str(skill), role, str(resp or ""))
    family_pack = get_evidence_pack(role_family)
    terms_pack = get_terminology_pack(str(skill), role, str(resp or ""))
    principles_pack = get_principles_pack(str(skill), role, str(resp or ""))
    calc_pack = q.get("calculation") or get_calculation_pack(str(skill), role, str(resp or ""))
    question_intent = detect_question_intent(
        q.get("question") or "",
        q.get("question_type"),
        category=q.get("category"),
    )
    terminology_terms = _terminology_terms_for_question(q, terms_pack, card, family_pack, str(skill))
    terms = [str(t.get("term")) for t in terminology_terms if isinstance(t, dict) and t.get("term")]
    standards = list(dict.fromkeys((card.get("standards") or []) + (exp.get("standards") or [])))
    domain_terms = list(
        dict.fromkeys(
            [str(t) for t in family_pack.get("domain_terms", [])]
            + terms
            + [str(s) for s in standards[:4]]
        )
    )
    domain_terms = [t for t in domain_terms if is_valid_key_term(str(t))]
    steps = _workflow_steps(family_pack, str(skill), role)
    steps = _sanitize_steps(steps)
    common_mistakes = (family_pack.get("common_mistakes") or exp.get("technical_pitfalls") or card.get("common_mistakes") or [])[:4]

    quality_checks = list(family_pack.get("verification_checks") or [])
    safety_checks = list(family_pack.get("safety_checks") or [])
    if not quality_checks:
        quality_checks = [
            "inspect output against required technical standard",
            "confirm readings are within permitted limits",
            "record measured test values correctly",
        ]
    if not safety_checks:
        safety_checks = [f"apply {s}" for s in standards[:2]] if standards else ["confirm safety prerequisites before execution"]

    definition = select_role_family_opening(role_family, role, title_case_skill(str(skill)))
    example = _pick_example(role, str(skill), family_pack, exp)
    closing = pick_intent_closing(role_family, question_intent, _pick_closing(role_family, family_pack, role, str(skill)))

    return {
        "direct_definition": definition,
        "practical_steps": [str(s) for s in steps],
        "standards_or_regulations": [str(s) for s in standards] or [f"{role_family.replace('_', ' ').title()} standards"],
        "tools_or_documents": domain_terms[:10],
        "safety_checks": safety_checks,
        "quality_checks": quality_checks[:4],
        "common_mistakes": [str(m) for m in common_mistakes],
        "role_specific_example": example,
        "interview_ready_closing": closing,
        "question_intent": question_intent,
        "role_family": role_family,
        "terminology_terms": terminology_terms[:8],
        "calculation_pack": calc_pack or {},
        "principles": _principles_for_question(principles_pack, family_pack, str(skill)),
    }


def validate_evidence_slots(slots: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    qtype = contract.get("question_type")
    if qtype in {"technical_explain", "scenario", "technical_general", "standards"}:
        if not slots.get("direct_definition"):
            failures.append("missing_direct_definition")
        if len(slots.get("practical_steps") or []) < 4:
            failures.append("missing_practical_steps")
        if not (slots.get("standards_or_regulations") or []):
            failures.append("missing_standards")
        if not (slots.get("safety_checks") or []):
            failures.append("missing_safety_checks")
        if not (slots.get("common_mistakes") or []):
            failures.append("missing_common_mistake")
        if len((slots.get("role_specific_example") or "").split()) < 25:
            failures.append("weak_example")
    return failures
