"""Sanitize local knowledge sources before they enter answers or study material."""

from __future__ import annotations

import re
from typing import Any

from app.agents.job_search.knowledge.domains import classify_skill_domain
from app.agents.job_search.knowledge.study_synthesis import infer_role_family, scrub_generic_phrasing
from app.agents.job_search.quality.blocked_phrase_guard import USING_DOC_PROCEDURES, contains_blocked_phrase
from app.agents.job_search.quality.surface_text_normalize import normalize_surface_text

_DOMAIN_FAMILY: dict[str, str] = {
    "engineering": "electrical",
    "technology": "technology",
    "healthcare": "healthcare",
    "hospitality_operations": "hospitality",
    "creative_media": "general",
    "legal_finance": "general",
    "education": "general",
    "social_care": "healthcare",
    "general_professional": "general",
}

_EXTRA_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (re.escape(USING_DOC_PROCEDURES), "role-specific quality checks and documented handover"),
    (
        re.escape("body of knowledge, tools, standards, and verified procedures"),
        "role-specific tools, standards, and verified procedures",
    ),
    (
        re.escape("The critical discipline is evidence"),
        "The critical discipline is measurable checks",
    ),
    (
        re.escape("When conditions change, I revalidate assumptions before proceeding"),
        "When conditions change, I re-check scope and constraints before proceeding",
    ),
)


def resolve_knowledge_role_family(
    *,
    role_title: str | None = None,
    skill: str | None = None,
    domain: str | None = None,
) -> str:
    if role_title or skill:
        job = {
            "title": role_title or "",
            "extracted_skills": [{"skill": skill}] if skill else [],
        }
        return infer_role_family(job)
    if domain:
        return _DOMAIN_FAMILY.get(domain, "general")
    return "general"


def sanitize_knowledge_text(
    text: str,
    *,
    role_title: str | None = None,
    skill: str | None = None,
    domain: str | None = None,
) -> str:
    if not text or not isinstance(text, str):
        return text
    family = resolve_knowledge_role_family(role_title=role_title, skill=skill, domain=domain)
    out = normalize_surface_text(text)
    out = scrub_generic_phrasing(out, family, skill)
    for pattern, replacement in _EXTRA_REPLACEMENTS:
        out = re.sub(pattern, replacement, out, flags=re.I)
    return normalize_surface_text(out)


def _sanitize_value(
    value: Any,
    *,
    role_title: str | None,
    skill: str | None,
    domain: str | None,
) -> Any:
    if isinstance(value, str):
        return sanitize_knowledge_text(
            value,
            role_title=role_title,
            skill=skill,
            domain=domain,
        )
    if isinstance(value, list):
        return [
            _sanitize_value(item, role_title=role_title, skill=skill, domain=domain)
            for item in value
        ]
    if isinstance(value, dict):
        return sanitize_knowledge_dict(
            value,
            role_title=role_title,
            skill=skill,
            domain=domain,
        )
    return value


def sanitize_knowledge_dict(
    data: dict[str, Any],
    *,
    role_title: str | None = None,
    skill: str | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    skill_name = skill or data.get("skill")
    domain_name = domain or data.get("domain")
    out: dict[str, Any] = {}
    for key, value in data.items():
        out[key] = _sanitize_value(
            value,
            role_title=role_title,
            skill=skill_name,
            domain=domain_name,
        )
    return out


def sanitize_skill_knowledge_entry(entry: dict[str, Any], role_hint: str | None = None) -> dict[str, Any]:
    skill = entry.get("skill")
    domain = entry.get("domain")
    return sanitize_knowledge_dict(
        dict(entry),
        role_title=role_hint,
        skill=skill,
        domain=domain,
    )


def sanitize_role_knowledge_entry(entry: dict[str, Any]) -> dict[str, Any]:
    role_title = entry.get("role_name")
    sanitized = sanitize_knowledge_dict(dict(entry), role_title=role_title)
    skill_expert = sanitized.get("skill_expert") or {}
    if isinstance(skill_expert, dict):
        cleaned: dict[str, Any] = {}
        for skill_key, expert in skill_expert.items():
            if isinstance(expert, dict):
                cleaned[skill_key] = sanitize_knowledge_dict(
                    expert,
                    role_title=role_title,
                    skill=expert.get("skill") or skill_key,
                    domain=classify_skill_domain(str(skill_key), role_title),
                )
            else:
                cleaned[skill_key] = expert
        sanitized["skill_expert"] = cleaned
    return sanitized


def sanitize_knowledge_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Sanitize a full skill_knowledge.json payload."""
    skills_out: dict[str, Any] = {}
    for key, entry in (payload.get("skills") or {}).items():
        if isinstance(entry, dict):
            skills_out[key] = sanitize_skill_knowledge_entry(entry)
        else:
            skills_out[key] = entry

    roles_out: dict[str, Any] = {}
    for key, entry in (payload.get("roles") or {}).items():
        if isinstance(entry, dict):
            roles_out[key] = sanitize_role_knowledge_entry(entry)
        else:
            roles_out[key] = entry

    return {
        **payload,
        "skills": skills_out,
        "roles": roles_out,
    }


def knowledge_text_is_clean(text: str) -> bool:
    return not contains_blocked_phrase(text)
