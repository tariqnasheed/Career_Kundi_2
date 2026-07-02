from __future__ import annotations

from typing import Any

from app.agents.job_search.knowledge.evidence_packs import get_evidence_pack, resolve_role_family
from app.agents.job_search.knowledge.normalize import normalize_key, title_case_skill


def create_question_contract(q: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]:
    role = job.get("title") or "Professional"
    role_family = resolve_role_family(role, q.get("role_family"))
    question = q.get("question") or ""
    skill = q.get("mapped_skill") or q.get("skill_tag") or "General"
    qtype = q.get("question_type") or "technical_general"
    card = q.get("skill_card") or {}
    pack = get_evidence_pack(role_family)

    if qtype in {"explain", "explain_to_peer"}:
        question_type = "technical_explain"
    elif qtype in {"scenario", "complex_problem"}:
        question_type = "scenario"
    elif qtype in {"terminology", "principles", "calculation", "procedure"}:
        question_type = "standards"
    else:
        question_type = "technical_general"

    required_terms = list(
        dict.fromkeys(
            [str(t) for t in (pack.get("domain_terms") or [])[:8]]
            + [str(t) for t in (card.get("core_concepts") or [])[:6]]
        )
    )
    standards = list(dict.fromkeys((card.get("standards") or []) + (pack.get("standards") or [])))

    min_terms = 4 if question_type in {"technical_explain", "scenario", "standards", "technical_general"} else 2

    return {
        "question": question,
        "role": role,
        "question_type": question_type,
        "mapped_skill": title_case_skill(skill),
        "mapped_skills": [title_case_skill(skill)] if skill else [],
        "role_family": role_family,
        "contract_id": f"{normalize_key(role)}::{normalize_key(str(skill))}::{question_type}",
        "required_domain_terms": required_terms,
        "minimum_domain_terms_required": min_terms if len(required_terms) >= min_terms else max(1, len(required_terms)),
        "must_include_standard": bool(standards),
        "must_include_common_mistake": True,
    }
