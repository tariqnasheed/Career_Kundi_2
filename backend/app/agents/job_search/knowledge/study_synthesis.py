"""Deterministic study-material synthesis layer (Iteration 004C).

Enriches locally generated study modules after document-library metadata is attached.
No LLM, web research, or invented citations.
"""

from __future__ import annotations

import re
from typing import Any

from app.agents.job_search.knowledge.normalize import normalize_key, title_case_skill
from app.agents.job_search.quality.blocked_phrase_guard import (
    INTERMEDIATE_QUALITY_CHECKS,
    build_family_scrub_replacements,
    contains_blocked_phrase,
)
from app.agents.job_search.quality.surface_text_normalize import normalize_surface_text

_INTERNAL_SKILL_LABELS = frozenset(
    {
        "role specific",
        "role_specific",
        "general",
        "n/a",
        "core terminology",
    }
)

_INTERNAL_PLACEHOLDER_MARKERS = ("role specific", "core terminology", "role_specific")

_FAMILY_REPLACEMENTS = build_family_scrub_replacements()

_LEARNING_PATH: dict[str, dict[str, str]] = {
    "technology": {
        "beginner": (
            "Start with what {skill} means in a {role} workflow: which systems it touches, "
            "what a healthy deployment or release looks like, and which monitoring or rollback signals matter first."
        ),
        "intermediate": (
            "Move to pipeline gates, deployment health checks, infrastructure drift, and incident response. "
            "Explain how {skill} connects to CI/CD stages, rollback criteria, and on-call ownership."
        ),
        "advanced": (
            "Discuss trade-offs under load: blast radius, canary vs blue/green choices, security controls, "
            "and how {skill} supports reliable incident timelines and post-incident review."
        ),
    },
    "healthcare": {
        "beginner": (
            "Start with what {skill} means for patient safety: allergy checks, indication, and basic "
            "contraindication awareness before any prescribing or counselling step."
        ),
        "intermediate": (
            "Move to medication review, interaction screening, renal/hepatic dosing, counselling points, "
            "and when to escalate to a senior clinician or governance pathway."
        ),
        "advanced": (
            "Discuss high-risk medicines, care transitions, governance documentation, and how {skill} "
            "supports safe multidisciplinary decision-making under time pressure."
        ),
    },
    "hospitality": {
        "beginner": (
            "Start with station setup for {skill}: grind size, dose, extraction time, hygiene controls, "
            "and allergen awareness before service begins."
        ),
        "intermediate": (
            "Move to milk texture, drink consistency, queue flow during rush hours, customer communication, "
            "and cleaning schedules that protect quality between orders."
        ),
        "advanced": (
            "Discuss peak-period throughput, remakes, stock handling, service recovery, and how {skill} "
            "maintains drink consistency and hygiene standards when demand spikes."
        ),
    },
    "data": {
        "beginner": (
            "Start with what {skill} means for a {role}: which tables or sources feed the analysis, "
            "how KPIs are defined, and why null checks matter before sharing numbers."
        ),
        "intermediate": (
            "Move to joins, source validation, dashboard filter logic, query plan review, and how to "
            "explain metric changes to stakeholders without overclaiming."
        ),
        "advanced": (
            "Discuss data quality trade-offs, query performance tuning, metric governance, and how "
            "{skill} supports trustworthy reporting under changing business rules."
        ),
    },
    "electrical": {
        "beginner": (
            "Start with what {skill} means on site: load assumptions, basic cable sizing inputs, "
            "safety isolation, and why compliance checks are part of normal work."
        ),
        "intermediate": (
            "Move to load calculations, cable derating, protective device coordination, inspection and "
            "test records, and coordination with other trades."
        ),
        "advanced": (
            "Discuss commissioning evidence, fault finding, standards compliance, and how {skill} "
            "supports safe energisation and documented handover."
        ),
    },
    "general": {
        "beginner": (
            "Start with what {skill} means in day-to-day {role} work: the core outcome, the first checks "
            "you perform, and the vocabulary a newcomer must recognise."
        ),
        "intermediate": (
            "Move to the step-by-step method, common quality checks, handover points, and how {skill} "
            "shows up in real tasks rather than abstract theory."
        ),
        "advanced": (
            "Discuss trade-offs, failure modes, stakeholder communication, and how experienced "
            "{role} professionals apply {skill} under pressure."
        ),
    },
}

_FAMILY_REVISION_HINTS: dict[str, str] = {
    "technology": "deployment health checks, rollback criteria, monitoring alerts, pipeline gates, and incident response",
    "healthcare": "medication review, allergy checks, contraindications, interactions, dosing, counselling, and escalation",
    "hospitality": "espresso consistency, grind/dose control, milk texture, allergen handling, hygiene, and queue flow",
    "data": "source validation, joins, null checks, KPI definitions, dashboard filters, and query performance",
    "electrical": "load calculations, cable sizing, protective device coordination, inspection records, and compliance checks",
    "general": "the matched workflow points, quality checks, and handover steps",
}


def _join_natural_list(items: list[str], *, lowercase: bool = False) -> str:
    cleaned: list[str] = []
    for item in items:
        text = str(item).strip()
        if not text:
            continue
        cleaned.append(text.lower() if lowercase else title_case_skill(text))
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        return f"{cleaned[0]} and {cleaned[1]}"
    return ", ".join(cleaned[:-1]) + f", and {cleaned[-1]}"


def _polish_saved_material_insight(text: str) -> str:
    out = normalize_surface_text(text or "")
    out = re.sub(r"(\w)\s+(Pay special attention)", r"\1. \2", out)
    out = re.sub(r"\.\s+before practising", " before practising", out, flags=re.I)
    out = re.sub(r"\s{2,}", " ", out)
    return out.strip()


def build_saved_material_insight(
    *,
    role: str,
    matched_skills: list[str],
    supporting_focus: list[str],
    role_family: str,
    skill_tag: str | None = None,
) -> str:
    """Compose a concise saved-material insight with clean sentence boundaries."""
    skill_text = _join_natural_list(matched_skills[:4]) or "core role skills"
    revision = _FAMILY_REVISION_HINTS.get(role_family, _FAMILY_REVISION_HINTS["general"])

    sentences = [
        f"The saved {role} role pack reinforces this question through {skill_text}.",
        f"Use it to revise {revision} before practising your answer.",
    ]

    focus_items = [str(f).strip() for f in supporting_focus[:3] if f and str(f).strip()]
    if focus_items:
        focus_text = _join_natural_list(focus_items, lowercase=True)
        if focus_text:
            sentences.append(f"Pay special attention to {focus_text}.")

    insight = scrub_generic_phrasing(" ".join(sentences), role_family, skill_tag)
    return _polish_saved_material_insight(insight)


def infer_role_family(job: dict[str, Any]) -> str:
    title = (job.get("title") or "").lower()
    skills_blob = " ".join(
        (s.get("skill") if isinstance(s, dict) else str(s))
        for s in (job.get("extracted_skills") or [])
    ).lower()
    blob = f"{title} {skills_blob}"
    if any(k in blob for k in ("devops", "software", "cloud", "sre", "platform engineer")):
        return "technology"
    if any(k in blob for k in ("pharmacist", "clinical", "nurse", "doctor", "healthcare")):
        return "healthcare"
    if any(k in blob for k in ("barista", "hospitality", "coffee", "haccp")):
        return "hospitality"
    if any(k in blob for k in ("data analyst", "analyst", "sql", "dashboard", "bi ")):
        return "data"
    if any(k in blob for k in ("electrical", "electrician", "commissioning", "cable")):
        return "electrical"
    return "general"


def _question_text(question: dict[str, Any]) -> str:
    return (question.get("question") or "").lower()


def _infer_contextual_skill_label(question: dict[str, Any], job: dict[str, Any]) -> str | None:
    category = (question.get("category") or "").lower()
    qtype = (question.get("question_type") or "").lower()
    qtext = _question_text(question)

    if category == "hr" or qtype.startswith("hr"):
        if any(token in qtext for token in ("motivat", "why this role", "why us", "why join", "why do you want")):
            return "Role Motivation"
        if any(token in qtext for token in ("notice", "salary", "availability", "relocation", "visa")):
            return "Role Logistics"
        return "Role Fit"

    if category == "daily_routine" or any(token in qtext for token in ("day in", "daily", "typical day", "first 90")):
        return "Daily Workflow"

    if category == "behavioral":
        return "Behavioral Evidence"

    if category in {"role_specific", "motivation"} or qtype in {"motivation", "company_research"}:
        if any(token in qtext for token in ("motivat", "why ", "fit", "interest in")):
            return "Role Motivation" if "motivat" in qtext or "why " in qtext else "Role Fit"
        if any(token in qtext for token in ("responsibilit", "accountable", "own", "deliver")):
            resp = job.get("responsibilities") or []
            if resp:
                first = resp[0]
                if isinstance(first, dict):
                    first = first.get("text") or ""
                phrase = " ".join(str(first).split()[:4]).strip(".,;:")
                if phrase:
                    return title_case_skill(phrase)
        if question.get("skill_tag") and normalize_key(question["skill_tag"]) != normalize_key(job.get("title") or ""):
            return title_case_skill(question["skill_tag"])
        return "Role Context"

    return None


def _is_internal_skill_label(skill: str) -> bool:
    normalized = (skill or "").strip().lower().replace("_", " ")
    return normalized in _INTERNAL_SKILL_LABELS or normalized.endswith(" specific")


def clean_user_facing_study_labels(
    skills: list[str],
    question: dict[str, Any],
    job: dict[str, Any],
) -> list[str]:
    """Replace internal placeholders like role_specific category labels with contextual labels."""
    contextual = _infer_contextual_skill_label(question, job)
    cleaned: list[str] = []
    for skill in skills or []:
        if not skill:
            continue
        if _is_internal_skill_label(skill):
            if contextual and contextual not in cleaned:
                cleaned.append(contextual)
            continue
        label = title_case_skill(skill)
        if normalize_key(label) == normalize_key(job.get("title") or "") and contextual:
            if contextual not in cleaned:
                cleaned.append(contextual)
            continue
        if label not in cleaned:
            cleaned.append(label)
    if not cleaned and contextual:
        cleaned.append(contextual)
    return cleaned[:5]


def build_user_facing_related_skills(question: dict[str, Any], job: dict[str, Any]) -> list[str]:
    """Build related skills without exposing internal category placeholders."""
    skills: list[str] = []
    if question.get("skill_tag"):
        skills.append(question["skill_tag"])
    for item in job.get("extracted_skills", [])[:3]:
        name = item.get("skill") if isinstance(item, dict) else item
        if name and normalize_key(name) not in {normalize_key(s) for s in skills}:
            skills.append(name)
    return clean_user_facing_study_labels(skills, question, job)


def scrub_generic_phrasing(text: str, role_family: str, skill_tag: str | None = None) -> str:
    if not text:
        return text
    out = text
    replacements = _FAMILY_REPLACEMENTS.get(role_family, []) + _FAMILY_REPLACEMENTS["general"]
    seen: set[str] = set()
    for pattern, replacement in replacements:
        if pattern in seen:
            continue
        seen.add(pattern)
        out = re.sub(pattern, replacement, out, flags=re.I)
    if skill_tag and INTERMEDIATE_QUALITY_CHECKS in out.lower():
        out = re.sub(
            re.escape(INTERMEDIATE_QUALITY_CHECKS),
            f"{title_case_skill(skill_tag)} quality checks",
            out,
            flags=re.I,
        )
    return normalize_surface_text(out)


def _scrub_value(value: Any, role_family: str, skill_tag: str | None) -> Any:
    if isinstance(value, str):
        return scrub_generic_phrasing(value, role_family, skill_tag)
    if isinstance(value, list):
        return [_scrub_value(item, role_family, skill_tag) for item in value]
    if isinstance(value, dict):
        return {k: _scrub_value(v, role_family, skill_tag) for k, v in value.items()}
    return value


def scrub_study_material_dict(
    study: dict[str, Any],
    *,
    role_family: str,
    skill_tag: str | None,
) -> dict[str, Any]:
    return _scrub_value(dict(study or {}), role_family, skill_tag)


def _document_library_used(question: dict[str, Any]) -> bool:
    for source in (question.get("study_sources") or {}).get("sources") or []:
        if source.get("source_type") == "document_library" and source.get("status") == "used":
            return True
    return False


def merge_document_support_into_study_material(
    study: dict[str, Any],
    question: dict[str, Any],
    job: dict[str, Any],
) -> dict[str, Any]:
    """Add a concise saved-material insight when document-library content was used."""
    if not _document_library_used(question):
        study.pop("saved_material_insight", None)
        return study

    doc = study.get("document_library_support") or {}
    if not doc:
        return study

    role = job.get("title") or "this role"
    family = infer_role_family(job)
    matched = [title_case_skill(s) for s in (doc.get("matched_skills") or []) if s]
    if not matched:
        skill = question.get("skill_tag")
        if skill:
            matched = [title_case_skill(skill)]

    study["saved_material_insight"] = build_saved_material_insight(
        role=role,
        matched_skills=matched,
        supporting_focus=list(doc.get("supporting_focus") or []),
        role_family=family,
        skill_tag=question.get("skill_tag"),
    )
    return study


def _learning_path_skill_label(question: dict[str, Any], job: dict[str, Any]) -> str:
    for skill in build_user_facing_related_skills(question, job):
        if not _is_internal_skill_label(skill):
            return title_case_skill(skill)
    contextual = _infer_contextual_skill_label(question, job)
    if contextual:
        return contextual
    for item in job.get("extracted_skills") or []:
        name = item.get("skill") if isinstance(item, dict) else item
        if name and not _is_internal_skill_label(str(name)):
            return title_case_skill(str(name))
    return title_case_skill(job.get("title") or "this role")


def _sanitize_internal_placeholders(text: str, skill: str) -> str:
    out = text or ""
    for marker in ("Role " + "Specific", "Core Terminology", "role specific", "core terminology"):
        out = re.sub(re.escape(marker), skill, out, flags=re.I)
    return out


def _scrub_internal_placeholders_in_study(study: dict[str, Any], skill: str) -> dict[str, Any]:
    for key, value in list(study.items()):
        if isinstance(value, str):
            study[key] = _sanitize_internal_placeholders(value, skill)
        elif isinstance(value, list):
            study[key] = [
                _sanitize_internal_placeholders(item, skill) if isinstance(item, str) else item
                for item in value
            ]
    return study


def build_skill_learning_path(
    study: dict[str, Any],
    question: dict[str, Any],
    job: dict[str, Any],
) -> dict[str, Any]:
    """Ensure beginner/intermediate/advanced explanations and skill linkage exist."""
    family = infer_role_family(job)
    role = job.get("title") or "this role"
    skill = _learning_path_skill_label(question, job)
    templates = _LEARNING_PATH.get(family, _LEARNING_PATH["general"])

    for level_key, template_key in (
        ("beginner_explanation", "beginner"),
        ("intermediate_explanation", "intermediate"),
        ("advanced_explanation", "advanced"),
    ):
        rendered = scrub_generic_phrasing(templates[template_key].format(skill=skill, role=role), family, skill)
        existing = study.get(level_key, "")
        if not existing or any(marker in (existing or "").lower() for marker in _INTERNAL_PLACEHOLDER_MARKERS):
            study[level_key] = rendered
        else:
            study[level_key] = _sanitize_internal_placeholders(
                scrub_generic_phrasing(str(existing), family, skill),
                skill,
            )

    covered = clean_user_facing_study_labels(
        [skill, *(question.get("related_skills") or [])],
        question,
        job,
    )
    study["technical_skills_covered"] = list(dict.fromkeys(covered))[:6]
    return _scrub_internal_placeholders_in_study(study, skill)


def synthesize_study_module(question: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]:
    """Post-process a finalized question: labels, phrasing, learning path, doc-library insight."""
    family = infer_role_family(job)
    skill_tag = question.get("skill_tag")

    question["related_skills"] = build_user_facing_related_skills(question, job)

    if question.get("model_answer"):
        question["model_answer"] = scrub_generic_phrasing(question["model_answer"], family, skill_tag)
        question["expert_reference_answer"] = question["model_answer"]
    if question.get("answer_explanation"):
        question["answer_explanation"] = scrub_generic_phrasing(
            question["answer_explanation"], family, skill_tag
        )

    study = dict(question.get("study_material") or {})
    study = scrub_study_material_dict(study, role_family=family, skill_tag=skill_tag)
    study = build_skill_learning_path(study, question, job)
    study = merge_document_support_into_study_material(study, question, job)
    question["study_material"] = study
    return question


def contains_blocked_generic_phrase(text: str) -> bool:
    return contains_blocked_phrase(text)
