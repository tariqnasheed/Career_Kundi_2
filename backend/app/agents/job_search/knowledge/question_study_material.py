"""Per-question study module finalization (Iteration 004E-E).

Connects each study module to the exact question, answer, and 004E-D source-ladder
metadata. Deterministic only — no live web or model API calls.
"""

from __future__ import annotations

import re
from typing import Any

from app.agents.job_search.knowledge.study_synthesis import (
    build_skill_learning_path,
    build_user_facing_related_skills,
    infer_role_family,
    scrub_generic_phrasing,
)
from app.agents.job_search.knowledge.study_material_budget import (
    apply_adaptive_study_budget,
    build_role_fit_apply_steps,
    build_role_fit_interview_application,
    question_has_role_fit_study_archetype,
)
from app.core.config import settings

_REQUIRED_TEXT_KEYS = (
    "core_idea",
    "what_this_question_tests",
    "beginner_explanation",
    "intermediate_explanation",
    "advanced_explanation",
    "interview_application",
)

_REQUIRED_LIST_KEYS = ("step_by_step_method", "common_mistakes", "key_principles")


def _first_sentence(text: str, *, max_len: int = 220) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    if not cleaned:
        return ""
    match = re.split(r"(?<=[.!?])\s+", cleaned, maxsplit=1)
    sentence = match[0] if match else cleaned
    if len(sentence) > max_len:
        # Trim trailing punctuation before the ellipsis and use the single-glyph "…"
        # so surface normalization (which collapses "...") cannot leave a ",." splice.
        cut = sentence[: max_len - 1].rsplit(" ", 1)[0].rstrip(" ,;:.")
        return (cut or sentence[: max_len - 1].rstrip(" ,;:.")) + "…"
    return sentence


def _source_items(question: dict[str, Any]) -> list[str]:
    items: list[str] = []
    for raw in question.get("question_source_items") or []:
        text = str(raw).strip()
        if text and text not in items:
            items.append(text)

    meta = question.get("generation_stage_meta") or {}
    for key in ("source_item_text", "coverage_item_text"):
        text = meta.get(key)
        if text and str(text).strip() and str(text).strip() not in items:
            items.append(str(text).strip())

    qtext = question.get("question") or ""
    for quoted in re.findall(r"'([^']{4,120})'", qtext):
        if quoted not in items:
            items.append(quoted)

    skill = question.get("skill_tag")
    if skill and str(skill).strip() and str(skill).strip() not in items:
        items.append(str(skill).strip())

    return items[:6]


def _build_what_this_question_tests(
    question: dict[str, Any],
    job: dict[str, Any],
    source_items: list[str],
) -> str:
    role = job.get("title") or "this role"
    item = source_items[0] if source_items else (question.get("skill_tag") or "the topic")
    category = (question.get("category") or "").lower()
    qtype = (question.get("question_type") or "").lower()
    qtext = (question.get("question") or "").lower()
    source_types = set(question.get("question_source_types") or [])

    if "company_research" in source_types or category == "company_specific":
        company = job.get("company_name") or "the employer"
        return (
            f"This question tests whether you can connect {item} to {company}'s captured "
            f"context as a {role} — not a generic answer that could fit any employer."
        )
    if qtype in {"tool_usage", "tool"} or "tool" in qtext:
        return (
            f"This question tests how you would use {item} on a typical {role} task and "
            f"validate output before handoff."
        )
    if qtype == "responsibility" or "responsibilit" in qtext or "first 30 days" in qtext:
        return (
            f"This question tests how you would approach '{item}' in the first weeks of a "
            f"{role} role with practical steps and quality checks."
        )
    if category == "behavioral":
        return (
            f"This behavioral question tests evidence of handling work related to {item} "
            f"using a clear Situation-Task-Action-Result structure."
        )
    return (
        f"This question tests applied understanding of {item} in {role} work — what you "
        f"would do, verify, and communicate to stakeholders."
    )


def _question_hook(question: dict[str, Any], *, max_len: int = 90) -> str:
    return _first_sentence(question.get("question") or "", max_len=max_len)


def _build_interview_application(
    question: dict[str, Any],
    job: dict[str, Any],
    source_items: list[str],
) -> str:
    role = job.get("title") or "this role"
    item = source_items[0] if source_items else (question.get("skill_tag") or "the focus area")
    return (
        f"Structure your spoken answer around {item}: state the goal, your method, checks "
        f"you would run, and the outcome a {role} interviewer expects to hear."
    )


def _company_source_insight(question: dict[str, Any], job: dict[str, Any]) -> str | None:
    source_types = set(question.get("question_source_types") or [])
    category = (question.get("category") or "").lower()
    if "company_research" not in source_types and category != "company_specific":
        return None

    cr = job.get("company_research")
    if not isinstance(cr, dict) or cr.get("research_confidence") in (None, "unavailable"):
        cp = job.get("company_profile") or {}
        summary = cp.get("summary") or cp.get("products_services")
        if summary:
            company = job.get("company_name") or "the company"
            return f"User-provided company context for {company}: {str(summary)[:200]}."
        return None

    company = job.get("company_name") or "the company"
    items = _source_items(question)
    focus = items[0] if items else None
    product = (cr.get("products_services") or [None])[0]
    industry = (cr.get("industries") or [None])[0]
    if not focus:
        focus = product or industry
    if not focus:
        overview = cr.get("company_overview")
        if overview:
            return f"Captured company overview for {company}: {str(overview)[:200]}."
        return None

    parts = [f"Use captured company research for {company}, focusing on {focus}."]
    if product and str(product) != str(focus):
        parts.append(f"Relevant offering: {product}.")
    if industry:
        parts.append(f"Industry context: {industry}.")
    return " ".join(parts)


def _document_library_insight(question: dict[str, Any]) -> str | None:
    study = question.get("study_material") or {}
    if study.get("saved_material_insight"):
        return str(study["saved_material_insight"])
    doc = study.get("document_library_support") or {}
    snippets = doc.get("snippets") or []
    if snippets:
        return str(snippets[0])
    note = doc.get("note")
    return str(note) if note else None


def _model_insight_text(question: dict[str, Any]) -> str | None:
    study = question.get("study_material") or {}
    if study.get("model_knowledge_insight"):
        return str(study["model_knowledge_insight"])
    mk = question.get("model_knowledge_support") or {}
    if mk.get("used") and mk.get("insight"):
        return str(mk["insight"])
    if not settings.job_search_enable_model_knowledge:
        return "Model knowledge is disabled by default in this build."
    status = str(mk.get("status") or "not_configured")
    if status == "not_configured":
        return "Model knowledge is not configured for this question."
    return None


def _study_source_status(question: dict[str, Any], job: dict[str, Any]) -> dict[str, str]:
    ladder = dict(question.get("source_status") or {})
    job_ladder = (job.get("source_ladder") or {}).get("source_status") or {}
    for key, value in job_ladder.items():
        ladder.setdefault(key, value)
    return {
        "user_fields": ladder.get("user_fields", "thin"),
        "link_extraction": ladder.get("link_extraction", "not_present"),
        "company_research": ladder.get("company_research") or ladder.get("web_research", "not_configured"),
        "model_knowledge": ladder.get("model_knowledge", "disabled"),
        "document_library": ladder.get("document_library", "not_configured"),
        "local_fallback": ladder.get("local_fallback", "used"),
    }


def _fallback_status_label(question: dict[str, Any]) -> str:
    used = (question.get("study_sources") or {}).get("used_source_types") or []
    if not used:
        return "local_fallback used"
    labels = []
    if "document_library" in used:
        labels.append("document_library used")
    if "local_fallback" in used:
        labels.append("local_fallback used")
    if "model" in used:
        labels.append("model knowledge used")
    return "; ".join(labels) if labels else "local_fallback used"


def _ensure_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if v and str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _empty_section_count(study: dict[str, Any]) -> int:
    missing = 0
    for key in _REQUIRED_TEXT_KEYS:
        if not str(study.get(key) or "").strip():
            missing += 1
    for key in _REQUIRED_LIST_KEYS:
        if not _ensure_list(study.get(key)):
            missing += 1
    return missing


def finalize_question_study_module(question: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]:
    """Build a finalized per-question study module with source-ladder trace metadata."""
    study = dict(question.get("study_material") or {})
    family = infer_role_family(job)
    skill_tag = question.get("skill_tag")
    source_items = _source_items(question)
    used_source_types = (question.get("study_sources") or {}).get("used_source_types") or []
    source_types = list(
        dict.fromkeys([*(question.get("question_source_types") or []), *used_source_types])
    )
    priority = list(question.get("source_priority_used") or [])

    study["question_id"] = question.get("question_id")
    study["question_text"] = question.get("question") or ""
    answer = question.get("model_answer") or ""
    study["answer_summary"] = _first_sentence(answer) if answer else ""
    study["source_items_used"] = source_items
    study["source_types_used"] = source_types
    study["source_priority_used"] = priority

    tests = study.get("what_this_question_tests") or _build_what_this_question_tests(
        question, job, source_items
    )
    hook = _question_hook(question)
    # Only append the question hook when the tests text does not already restate the
    # question. The answer-builder "what_this_question_tests" already embeds a
    # (word-truncated) copy of the question, so appending a second truncated copy
    # produced splices like "…handling 'Medicat It directly addresses: Describe…".
    tests_norm = re.sub(r"\s+", " ", tests).lower()
    q_lead = re.sub(r"\s+", " ", question.get("question") or "").strip().lower()[:40]
    if hook and q_lead and q_lead not in tests_norm:
        tests = f"{tests} It directly addresses: {hook}"
    study["what_this_question_tests"] = scrub_generic_phrasing(tests, family, skill_tag)
    study["core_idea"] = scrub_generic_phrasing(
        study.get("core_idea") or study.get("overview") or study["what_this_question_tests"],
        family,
        skill_tag,
    )

    if not study.get("key_definitions") and study.get("definitions"):
        study["key_definitions"] = list(study["definitions"])
    raw_principles = _ensure_list(
        study.get("key_principles") or study.get("principles") or study.get("key_concepts")
        or question.get("ideal_answer_points")
    )
    category = (question.get("category") or "").lower()
    qtext = (question.get("question") or "").lower()
    is_role_fit = question_has_role_fit_study_archetype(question)
    is_company_or_motivation = is_role_fit or (
        category == "company_specific"
        or "company_research" in set(question.get("question_source_types") or [])
        or any(
            k in qtext
            for k in (
                "excites you",
                "why do you want",
                "why this role",
                "why are you interested",
                "experience help",
                "motivat",
                "fit for this",
                "a good fit",
            )
        )
    )
    # Terse checklist points (e.g. company_specific `ideal_answer_points` such as
    # "References X") are coverage cues, not substantive study principles. For a
    # company/role-fit question, expand them into genuine role-fit guidance (§10/§15)
    # rather than leaving a non-substantive key_principles element. This is guidance,
    # not invented user history — it never asserts the user did anything.
    substantive_raw = [p for p in raw_principles if len(str(p).split()) >= 4]
    if is_company_or_motivation and len(substantive_raw) < 2:
        company = job.get("company_name") or "the employer"
        role = job.get("title") or "this role"
        focus = source_items[0] if source_items else (skill_tag or "the role's core work")
        study["key_principles"] = [
            f"Explain why {company} and this {role} role genuinely fit your interests and strengths.",
            f"Connect your real experience with {focus} to what the posting actually asks for.",
            "Name the contribution you could make and the development direction you want in the role.",
        ]
    elif raw_principles:
        study["key_principles"] = raw_principles
    elif is_role_fit:
        role = job.get("title") or "this role"
        focus = source_items[0] if source_items else (job.get("responsibilities") or ["core duties"])[0]
        if isinstance(focus, dict):
            focus = focus.get("text")
        study["key_principles"] = [
            f"Explain why this {role} posting genuinely fits your interests and strengths.",
            f"Connect {str(focus).lower()} to what attracts you and where you hope to contribute.",
            "State development direction honestly — do not invent employers, projects, or metrics.",
        ]
    else:
        focus = source_items[0] if source_items else (skill_tag or "the focus area")
        study["key_principles"] = [
            f"Tie each point back to {focus} and the exact wording of the question.",
            "State assumptions, method, validation checks, and expected outcome.",
        ]

    if not study.get("common_mistakes"):
        study["common_mistakes"] = _ensure_list(question.get("common_mistakes")) or [
            "Answering without naming the specific skill or tool being tested.",
            "Skipping validation or quality checks relevant to the task.",
            "Giving a generic example that does not match the question wording.",
        ]

    if not is_role_fit and not all(
        str(study.get(k) or "").strip()
        for k in ("beginner_explanation", "intermediate_explanation", "advanced_explanation")
    ):
        study = build_skill_learning_path(study, question, job)

    if is_role_fit:
        study["step_by_step_method"] = build_role_fit_apply_steps(question, job)
    elif not study.get("step_by_step_method"):
        study["step_by_step_method"] = _ensure_list(
            study.get("step_by_step_breakdown") or study.get("step_by_step_method")
        )

    covered = study.get("technical_or_workflow_skills_covered") or study.get("technical_skills_covered")
    if not covered:
        covered = build_user_facing_related_skills(question, job)
    study["technical_or_workflow_skills_covered"] = covered[:6]

    if is_role_fit:
        study["interview_application"] = scrub_generic_phrasing(
            build_role_fit_interview_application(question, job),
            family,
            skill_tag,
        )
    else:
        study["interview_application"] = scrub_generic_phrasing(
            study.get("interview_application") or _build_interview_application(question, job, source_items),
            family,
            skill_tag,
        )

    follow_ups = question.get("follow_up_questions") or question.get("follow_ups") or []
    study["likely_follow_ups"] = [str(f).strip() for f in follow_ups if f and str(f).strip()][:4]

    company_insight = _company_source_insight(question, job)
    if company_insight:
        study["web_or_company_source_insight"] = scrub_generic_phrasing(company_insight, family, skill_tag)

    doc_insight = _document_library_insight(question)
    if doc_insight:
        study["document_library_insight"] = scrub_generic_phrasing(doc_insight, family, skill_tag)
        study.setdefault("saved_material_insight", study["document_library_insight"])

    model_insight = _model_insight_text(question)
    if model_insight:
        study["model_insight"] = scrub_generic_phrasing(model_insight, family, skill_tag)

    study["source_status"] = _study_source_status(question, job)
    study["fallback_status"] = _fallback_status_label(question)

    study = apply_adaptive_study_budget(study, question, job)

    return study


def apply_finalized_study_module(question: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]:
    """Attach finalized study module to a question after source metadata is present."""
    question["study_material"] = finalize_question_study_module(question, job)
    return question


def study_module_fingerprint(study: dict[str, Any], question_text: str = "") -> str:
    """Compact fingerprint for duplicate-module detection."""
    parts = [
        str(study.get("question_id") or ""),
        question_text[:100].lower().strip(),
        str(study.get("what_this_question_tests") or ""),
        str(study.get("core_idea") or ""),
        "|".join(_ensure_list(study.get("step_by_step_method"))[:3]),
        str(study.get("interview_application") or ""),
    ]
    return " ".join(parts).lower().strip()


def count_empty_study_sections(study: dict[str, Any]) -> int:
    from app.agents.job_search.knowledge.study_material_budget import (
        _DEPTH_CONTRACT,
        _element_present,
    )

    depth = study.get("study_depth")
    if depth and depth in _DEPTH_CONTRACT:
        required = list(_DEPTH_CONTRACT[depth])
        for key in ("core_idea", "what_this_question_tests"):
            if key not in required:
                required.append(key)
        return sum(1 for el in required if not _element_present(study, el))
    return _empty_section_count(study)
