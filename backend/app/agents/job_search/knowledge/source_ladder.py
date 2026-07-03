"""Full interview-pack source ladder integration (Iteration 004E-D).

Priority (highest first):
1. User-provided job fields
2. Job posting URL extraction (004E-B)
3. Company profile research (004E-C)
4. Model knowledge (feature-flagged)
5. Document library
6. Local deterministic fallback

No network fetching in this module — reuses existing 004E-B/004E-C metadata only.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from app.agents.job_search.job_intelligence import JobIntelligenceItem, JobIntelligenceProfile
from app.core.config import settings

SOURCE_PRIORITY = (
    "user_field",
    "job_posting_extraction",
    "company_research",
    "model_knowledge",
    "document_library",
    "local_fallback",
)

SOURCE_LABELS: dict[str, str] = {
    "user_field": "User-provided job fields",
    "job_posting_extraction": "Job posting URL extraction",
    "company_research": "Company profile research",
    "model_knowledge": "Model knowledge",
    "document_library": "Document library",
    "local_fallback": "Local deterministic fallback",
    "company_page": "Company profile page",
    "job_posting_derived": "Job posting derived company context",
    "parsed_description": "Parsed job description",
    "extracted_skill": "Extracted skill",
}

_ITEM_ID_COUNTER = 0


def _next_item_id(prefix: str) -> str:
    global _ITEM_ID_COUNTER  # noqa: PLW0603
    _ITEM_ID_COUNTER += 1
    return f"{prefix}-{_ITEM_ID_COUNTER}"


def _norm(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def _dedupe_key(text: str) -> str:
    return _norm(text).lower()


def _source_label(source_type: str) -> str:
    return SOURCE_LABELS.get(source_type, source_type.replace("_", " ").title())


@dataclass
class SourceLadderContext:
    source_status: dict[str, str] = field(default_factory=dict)
    source_priority_used: list[str] = field(default_factory=list)
    document_library_path: str | None = None


def _user_fields_status(profile: JobIntelligenceProfile) -> str:
    signal = bool(
        profile.job_description
        or profile.responsibilities
        or profile.required_skills
        or profile.company_profile
        or profile.extra_notes
    )
    return "used" if signal else "thin"


def _link_extraction_status(profile: JobIntelligenceProfile, job: dict[str, Any]) -> str:
    extraction = job.get("job_posting_extraction") if isinstance(job.get("job_posting_extraction"), dict) else None
    if profile.extracted_link_content or (
        extraction and extraction.get("extraction_confidence") not in (None, "failed")
    ):
        return "used"
    if extraction and extraction.get("extraction_confidence") == "failed":
        return "unavailable"
    if profile.job_posting_url or job.get("source_url"):
        return "not_configured"
    return "not_present"


def _company_research_status(job: dict[str, Any]) -> str:
    cr = job.get("company_research")
    if not isinstance(cr, dict):
        return "not_configured"
    confidence = cr.get("research_confidence")
    ss = cr.get("source_status") or {}
    if ss.get("company_page") == "used" and confidence in ("high", "medium"):
        return "used"
    if ss.get("company_page") == "failed":
        return "unavailable"
    if confidence in ("high", "medium", "low"):
        return "used" if ss.get("user_company_profile") == "used" else "available_not_used"
    return "unavailable"


def _model_knowledge_status() -> str:
    if settings.job_search_enable_model_knowledge:
        return "available_not_used"
    return "disabled"


def _document_library_status(job: dict[str, Any]) -> str:
    ladder = job.get("source_ladder")
    if isinstance(ladder, dict):
        persisted = (ladder.get("source_status") or {}).get("document_library")
        if persisted == "used" or ladder.get("document_library_used"):
            return "used"
        if ladder.get("document_library_path"):
            return "available_not_used"
    from app.agents.job_search.knowledge.document_library_retriever import find_role_study_documents

    pack = find_role_study_documents(str(job.get("title") or ""))
    if pack and pack.get("folder"):
        return "available_not_used"
    return "not_configured"


def build_source_ladder_status(
    job: dict[str, Any],
    profile: JobIntelligenceProfile | None = None,
) -> dict[str, str]:
    """Build transparent 6-tier source ladder status without network calls."""
    if profile is None:
        from app.agents.job_search.job_intelligence import build_job_intelligence_profile

        profile = build_job_intelligence_profile(job)

    doc_path: str | None = None
    try:
        from app.agents.job_search.knowledge.document_library_retriever import find_role_study_documents

        pack = find_role_study_documents(str(job.get("title") or ""))
        if pack:
            doc_path = pack.get("folder") or pack.get("path")
    except Exception:  # noqa: BLE001
        doc_path = None

    if doc_path:
        job.setdefault("source_ladder", {})["document_library_path"] = doc_path

    status = {
        "user_fields": _user_fields_status(profile),
        "link_extraction": _link_extraction_status(profile, job),
        "company_research": _company_research_status(job),
        "model_knowledge": _model_knowledge_status(),
        "document_library": _document_library_status(job),
        "local_fallback": "used",
        # Backward-compatible alias used by earlier iterations
        "web_research": _company_research_status(job),
    }
    persisted = (job.get("source_ladder") or {}).get("source_status") or {}
    for tier in ("link_extraction", "company_research", "document_library"):
        if persisted.get(tier) == "used":
            status[tier] = "used"
    if persisted.get("web_research") == "used":
        status["web_research"] = "used"
    return status


def build_source_ladder_context(
    job: dict[str, Any],
    profile: JobIntelligenceProfile | None = None,
) -> SourceLadderContext:
    if profile is None:
        from app.agents.job_search.job_intelligence import build_job_intelligence_profile

        profile = build_job_intelligence_profile(job)
    status = build_source_ladder_status(job, profile)
    used: list[str] = []
    for tier in ("user_fields", "link_extraction", "company_research", "model_knowledge", "document_library"):
        if status.get(tier) == "used":
            key = tier.replace("_fields", "_field").replace("link_extraction", "job_posting_extraction")
            if key == "user_field":
                used.append("user_field")
            elif key == "job_posting_extraction":
                used.append("job_posting_extraction")
            elif key == "company_research":
                used.append("company_research")
            elif key == "model_knowledge":
                used.append("model_knowledge")
            elif key == "document_library":
                used.append("document_library")
    if status.get("local_fallback") == "used":
        used.append("local_fallback")
    ladder_path = (job.get("source_ladder") or {}).get("document_library_path")
    return SourceLadderContext(
        source_status=status,
        source_priority_used=used,
        document_library_path=ladder_path,
    )


def ladder_context_to_dict(ctx: SourceLadderContext) -> dict[str, Any]:
    return asdict(ctx)


def _question_uses_document_library(question: dict[str, Any]) -> bool:
    for entry in (question.get("study_sources") or {}).get("sources") or []:
        if isinstance(entry, dict) and entry.get("source_type") == "document_library":
            if entry.get("status") == "used":
                return True
    return False


def _question_uses_company_research(question: dict[str, Any]) -> bool:
    if "company_research" in (question.get("question_source_types") or []):
        return True
    meta = question.get("generation_stage_meta") or {}
    return meta.get("source_type") == "company_research"


def refresh_source_ladder_usage_from_questions(
    job: dict[str, Any],
    questions: list[dict[str, Any]],
) -> None:
    """Promote ladder tiers to ``used`` when finalized questions actually cite them."""
    if not questions:
        return
    ladder = job.setdefault("source_ladder", {})
    status = dict(ladder.get("source_status") or build_source_ladder_status(job))
    priority = list(ladder.get("source_priority_used") or [])

    if any(_question_uses_company_research(q) for q in questions):
        cr = job.get("company_research")
        if isinstance(cr, dict) and cr.get("research_confidence") not in (None, "unavailable"):
            status["company_research"] = "used"
            status["web_research"] = "used"
            if "company_research" not in priority:
                priority.append("company_research")

    if any(_question_uses_document_library(q) for q in questions):
        status["document_library"] = "used"
        ladder["document_library_used"] = True
        if "document_library" not in priority:
            priority.append("document_library")

    ladder["source_status"] = status
    ladder["source_priority_used"] = priority


def apply_source_ladder_to_job(job: dict[str, Any]) -> SourceLadderContext:
    ctx = build_source_ladder_context(job)
    job["source_ladder"] = ladder_context_to_dict(ctx)
    return ctx


def _existing_texts(items: list[JobIntelligenceItem]) -> set[str]:
    return {_dedupe_key(i.text) for i in items if i.text}


def collect_source_derived_items(
    job: dict[str, Any],
    existing_items: list[JobIntelligenceItem],
) -> list[JobIntelligenceItem]:
    """Append audit items from URL extraction and company research without duplicating user fields."""
    seen = _existing_texts(existing_items)
    extra: list[JobIntelligenceItem] = []

    def add(item_type: str, text: str, source: str, importance: str) -> None:
        key = _dedupe_key(text)
        if not key or key in seen:
            return
        seen.add(key)
        extra.append(
            JobIntelligenceItem(
                item_type=item_type,
                text=_norm(text),
                source=source,
                importance=importance,
            )
        )

    extraction = job.get("job_posting_extraction")
    if isinstance(extraction, dict) and extraction.get("extraction_confidence") not in (None, "failed"):
        for resp in extraction.get("responsibilities") or []:
            add("responsibility", str(resp), "job_posting_extraction", "high")
        for req in (extraction.get("requirements") or []) + (extraction.get("preferred_qualifications") or []):
            add("required_skill", str(req), "job_posting_extraction", "medium")
        for tool in extraction.get("tools") or []:
            add("tool", str(tool), "job_posting_extraction", "high")
        for skill in extraction.get("skills") or []:
            add("required_skill", str(skill), "job_posting_extraction", "medium")

    cr = job.get("company_research")
    if isinstance(cr, dict) and cr.get("research_confidence") not in (None, "unavailable"):
        if cr.get("company_overview"):
            add("company_profile", str(cr["company_overview"]), "company_research", "high")
        for product in cr.get("products_services") or []:
            add("company_product_service", str(product), "company_research", "high")
        for industry in cr.get("industries") or []:
            add("company_industry", str(industry), "company_research", "medium")
        for market in cr.get("markets") or []:
            add("company_market", str(market), "company_research", "medium")
        for mission in cr.get("mission_or_values") or []:
            add("company_profile", str(mission), "company_research", "medium")

    if job.get("extra_notes"):
        add("user_note", str(job["extra_notes"]), "user_field", "medium")

    for item in extra:
        item.item_id = _next_item_id(item.item_type[:4])
        item.source_label = _source_label(item.source)
    return extra


def assign_item_ids(items: list[JobIntelligenceItem]) -> None:
    for item in items:
        if not getattr(item, "item_id", None):
            item.item_id = _next_item_id(item.item_type[:4])
        if not getattr(item, "source_label", None):
            item.source_label = _source_label(item.source)


def _shorten(text: str, max_len: int = 90) -> str:
    text = _norm(text)
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rsplit(" ", 1)[0] + "..."


def build_source_ladder_questions(job: dict[str, Any], ctx: SourceLadderContext) -> list[dict[str, Any]]:
    """Generate additional questions grounded in URL extraction, company research, and document library."""
    questions: list[dict[str, Any]] = []
    role = job.get("title") or "this role"
    company = job.get("company_name") or "the company"

    extraction = job.get("job_posting_extraction")
    if isinstance(extraction, dict) and ctx.source_status.get("link_extraction") == "used":
        for resp in (extraction.get("responsibilities") or [])[:3]:
            text = _shorten(str(resp))
            questions.append(
                {
                    "category": "role_specific",
                    "question": (
                        f"The job posting lists '{text}' as a responsibility. "
                        f"How would you approach this in your first 30 days as a {role}?"
                    ),
                    "why_asked": "Source ladder: responsibility from job posting URL extraction.",
                    "ideal_answer_points": [f"References {text}", "Explains practical steps", "Includes quality checks"],
                    "question_type": "responsibility",
                    "skill_tag": role,
                    "generation_stage_meta": {
                        "stage_3_source_ladder": True,
                        "source_type": "job_posting_extraction",
                        "source_item_text": text,
                    },
                }
            )
        for tool in (extraction.get("tools") or [])[:2]:
            text = _shorten(str(tool))
            questions.append(
                {
                    "category": "technical",
                    "question": (
                        f"The posting mentions {text}. How would you use {text} on a typical {role} task "
                        f"and validate the output before handoff?"
                    ),
                    "why_asked": "Source ladder: tool from job posting URL extraction.",
                    "ideal_answer_points": [f"Uses {text}", "Explains workflow", "Includes validation"],
                    "question_type": "tool_usage",
                    "skill_tag": text,
                    "generation_stage_meta": {
                        "stage_3_source_ladder": True,
                        "source_type": "job_posting_extraction",
                        "source_item_text": text,
                    },
                }
            )

    cr = job.get("company_research")
    if isinstance(cr, dict) and ctx.source_status.get("company_research") in ("used", "available_not_used"):
        for product in (cr.get("products_services") or [])[:2]:
            text = _shorten(str(product))
            questions.append(
                {
                    "category": "company_specific",
                    "question": (
                        f"Based on researched company context, how would you contribute to {company}'s "
                        f"{text} offering in this {role} role?"
                    ),
                    "why_asked": "Source ladder: company product/service from company research.",
                    "ideal_answer_points": [f"References {text}", "Links to role deliverables"],
                    "question_type": "company_context",
                    "skill_tag": role,
                    "generation_stage_meta": {
                        "stage_3_source_ladder": True,
                        "source_type": "company_research",
                        "source_item_text": text,
                    },
                }
            )
        for industry in (cr.get("industries") or [])[:1]:
            text = _shorten(str(industry))
            questions.append(
                {
                    "category": "company_specific",
                    "question": (
                        f"What {text} domain challenges should a {role} at {company} plan for, "
                        f"based on available company research?"
                    ),
                    "why_asked": "Source ladder: industry context from company research.",
                    "ideal_answer_points": [f"Names a {text} challenge", "Connects to role work"],
                    "question_type": "industry_domain",
                    "skill_tag": role,
                    "generation_stage_meta": {
                        "stage_3_source_ladder": True,
                        "source_type": "company_research",
                        "source_item_text": text,
                    },
                }
            )
        for market in (cr.get("markets") or [])[:1]:
            text = _shorten(str(market))
            questions.append(
                {
                    "category": "company_specific",
                    "question": (
                        f"How would serving the {text} market change your priorities as a {role} at {company}?"
                    ),
                    "why_asked": "Source ladder: market context from company research.",
                    "ideal_answer_points": [f"References {text}", "Explains market-aware tradeoffs"],
                    "question_type": "company_market",
                    "skill_tag": role,
                    "generation_stage_meta": {
                        "stage_3_source_ladder": True,
                        "source_type": "company_research",
                        "source_item_text": text,
                    },
                }
            )

    return questions


def annotate_question_source_metadata(question: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]:
    """Attach source ladder trace metadata to a question for audit and 004E-E handoff."""
    meta = question.get("generation_stage_meta") or {}
    source_items: list[str] = []
    source_types: list[str] = []
    coverage_ids: list[str] = []

    if meta.get("stage_4_coverage_audit"):
        text = meta.get("coverage_item_text")
        stype = "user_field"
        if text:
            source_items.append(str(text))
        source_types.append(stype)
        if text:
            coverage_ids.append(f"coverage-{_dedupe_key(str(text))[:24]}")

    if meta.get("stage_3_source_ladder"):
        text = meta.get("source_item_text")
        stype = str(meta.get("source_type") or "local_fallback")
        if text:
            source_items.append(str(text))
        if stype not in source_types:
            source_types.append(stype)

    if meta.get("profile_driven"):
        source_types.append("user_field")

    skill = question.get("skill_tag")
    if skill and not source_items:
        source_items.append(str(skill))
    if not source_types:
        source_types.append("local_fallback")

    ladder = job.get("source_ladder") or {}
    priority = list(ladder.get("source_priority_used") or [])
    if not priority:
        ctx = build_source_ladder_context(job)
        priority = ctx.source_priority_used

    question["question_source_items"] = source_items
    question["question_source_types"] = list(dict.fromkeys(source_types))
    question["source_priority_used"] = priority
    question["source_status"] = dict(ladder.get("source_status") or build_source_ladder_status(job))
    question["coverage_item_ids"] = coverage_ids
    return question


def build_coverage_audit_items(profile: JobIntelligenceProfile) -> list[dict[str, Any]]:
    """Serialize all trackable items with source metadata for API/export."""
    assign_item_ids(profile.extracted_items)
    rows: list[dict[str, Any]] = []
    for item in profile.extracted_items:
        if item.importance not in ("critical", "high", "medium"):
            continue
        rows.append(
            {
                "item_id": getattr(item, "item_id", None) or _next_item_id(item.item_type[:4]),
                "item_type": item.item_type,
                "item_text": item.text,
                "source_type": item.source,
                "source_label": getattr(item, "source_label", None) or _source_label(item.source),
                "covered": item.covered,
                "related_question_ids": list(item.related_question_ids),
                "missing_reason": item.missing_reason,
                "action": "covered" if item.covered else "add_question",
            }
        )
    return rows
