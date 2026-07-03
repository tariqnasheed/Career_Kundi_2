"""Interview pack coverage audit and missing-item question generation (Iteration 004E-A)."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from app.agents.job_search.job_intelligence import JobIntelligenceItem, JobIntelligenceProfile

_PROGRESSION_LABELS = ("basic", "practical", "scenario", "advanced", "senior")
_PROGRESSION_TO_DIFFICULTY = {
    "basic": "Easy",
    "practical": "Medium",
    "scenario": "Medium",
    "advanced": "Hard",
    "senior": "Expert",
}


@dataclass
class CoverageAuditResult:
    total_items: int
    covered_items: int
    missing_items: list[JobIntelligenceItem]
    coverage_score: int
    warnings: list[str] = field(default_factory=list)
    added_question_count: int = 0
    responsibilities_covered: int = 0
    skills_covered: int = 0
    tools_covered: int = 0
    company_context_covered: bool = False
    compliance_covered: bool = False
    has_difficulty_progression: bool = False
    has_practical_or_scenario: bool = False


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]{3,}", _norm(text)) if len(t) > 2}


def _item_covered(item: JobIntelligenceItem, question_blob: str, question_ids: list[tuple[str, str]]) -> tuple[bool, list[str]]:
    item_tokens = _tokens(item.text)
    if not item_tokens:
        return False, []
    blob_tokens = _tokens(question_blob)
    overlap = item_tokens & blob_tokens
    if len(overlap) >= max(1, min(2, len(item_tokens))):
        matched_ids = [qid for qid, qtext in question_ids if _tokens(qtext) & item_tokens]
        return True, matched_ids
    if _norm(item.text) in _norm(question_blob):
        matched_ids = [qid for qid, qtext in question_ids if _norm(item.text) in _norm(qtext)]
        return True, matched_ids
    return False, []


def audit_pack_coverage(profile: JobIntelligenceProfile, questions: list[dict[str, Any]]) -> CoverageAuditResult:
    question_blob = " ".join(_norm(q.get("question", "")) for q in questions)
    question_ids = [
        (str(q.get("question_id") or f"q-{i}"), str(q.get("question") or ""))
        for i, q in enumerate(questions)
    ]
    missing: list[JobIntelligenceItem] = []
    covered_count = 0
    resp_covered = 0
    skills_covered = 0
    tools_covered = 0
    company_covered = False
    compliance_covered = False

    for item in profile.extracted_items:
        if item.importance not in ("critical", "high", "medium"):
            continue
        ok, related = _item_covered(item, question_blob, question_ids)
        item.covered = ok
        item.related_question_ids = related
        if ok:
            covered_count += 1
            if item.item_type in ("responsibility", "daily_responsibility"):
                resp_covered += 1
            elif item.item_type in ("required_skill", "technical_skill", "preferred_skill"):
                skills_covered += 1
            elif item.item_type == "tool":
                tools_covered += 1
            elif item.item_type in ("company_profile", "company_products", "industry_domain", "company_product_service", "company_industry", "company_market"):
                company_covered = True
            elif item.item_type == "compliance":
                compliance_covered = True
        else:
            clone = JobIntelligenceItem(
                item_type=item.item_type,
                text=item.text,
                source=item.source,
                importance=item.importance,
                covered=False,
                missing_reason="No exportable question referenced this item closely enough.",
                item_id=getattr(item, "item_id", None),
                source_label=getattr(item, "source_label", None),
            )
            missing.append(clone)

    trackable = [i for i in profile.extracted_items if i.importance in ("critical", "high", "medium")]
    total = len(trackable)
    if total == 0:
        score = 0
    else:
        score = int(round((covered_count / total) * 100))

    progression = {str((q.get("generation_stage_meta") or {}).get("progression_label") or "") for q in questions}
    has_progression = len(progression & set(_PROGRESSION_LABELS)) >= 2
    has_practical = any(
        (q.get("generation_stage_meta") or {}).get("progression_label") in ("practical", "scenario")
        or q.get("question_type") in ("scenario", "practical_task", "case_study")
        for q in questions
    )

    warnings: list[str] = []
    if total == 0:
        warnings.append(
            "No detailed job intelligence items were available to audit. "
            "Add responsibilities, skills, tools, and company details for a meaningful coverage audit."
        )
    elif profile.completeness_score <= 30:
        warnings.append("Input completeness is weak — coverage audit may be limited.")
    if missing and profile.completeness_score > 60:
        warnings.append(f"{len(missing)} important profile items were not yet covered by exportable questions.")

    return CoverageAuditResult(
        total_items=total,
        covered_items=covered_count,
        missing_items=missing,
        coverage_score=score,
        warnings=warnings,
        responsibilities_covered=resp_covered,
        skills_covered=skills_covered,
        tools_covered=tools_covered,
        company_context_covered=company_covered,
        compliance_covered=compliance_covered or not profile.compliance_safety_ethics,
        has_difficulty_progression=has_progression,
        has_practical_or_scenario=has_practical,
    )


def _shorten(text: str, max_len: int = 90) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rsplit(" ", 1)[0] + "..."


def _question_for_item(item: JobIntelligenceItem, profile: JobIntelligenceProfile, progression: str) -> dict[str, Any]:
    role = profile.job_title
    company = profile.company_name or "the company"
    text = _shorten(item.text)

    if item.item_type in ("responsibility", "daily_responsibility"):
        question = (
            f"How would you handle {text} in this {role} role while balancing quality, "
            f"deadlines, and stakeholder expectations?"
        )
        category = "role_specific"
        qtype = "responsibility"
    elif item.item_type == "tool":
        resp = profile.responsibilities[0] if profile.responsibilities else text
        question = (
            f"How would you use {text} to complete {_shorten(resp, 70)}, and what checks would you "
            f"perform before sharing the result?"
        )
        category = "technical"
        qtype = "tool_usage"
    elif item.item_type in ("company_profile", "company_products", "industry_domain", "company_product_service", "company_industry", "company_market"):
        focus = text or profile.company_products_services or profile.industry_domain or company
        question = (
            f"How would you adapt your work as a {role} if the company's main focus is {focus}?"
        )
        category = "company_specific"
        qtype = "company_context"
    elif item.item_type == "compliance":
        task = profile.responsibilities[0] if profile.responsibilities else text
        question = (
            f"What safety, ethics, or compliance risks would you check before completing "
            f"{_shorten(task, 70)} in this {role} role?"
        )
        category = "role_specific"
        qtype = "compliance"
    elif item.item_type in ("required_skill", "technical_skill", "preferred_skill"):
        question = (
            f"Walk through how you would apply {text} on a realistic {role} task, including setup, "
            f"execution checks, and how you would explain the result to stakeholders."
        )
        category = "technical"
        qtype = "skill_application"
    else:
        question = (
            f"In this {role} role, how would you demonstrate competence in {text} during a real work week?"
        )
        category = "role_specific"
        qtype = "profile_item"

    if item.item_type == "tool":
        skill_tag = text
    elif item.item_type in ("required_skill", "technical_skill", "preferred_skill"):
        skill_tag = text
    else:
        skill_tag = role

    return {
        "category": category,
        "question": question,
        "why_asked": f"Coverage audit added this question to cover a missing {item.item_type.replace('_', ' ')} from the job profile.",
        "ideal_answer_points": [
            f"References {text} directly",
            "Explains practical steps and quality checks",
            f"Connects the answer to {role} responsibilities",
        ],
        "skill_tag": skill_tag,
        "question_type": qtype,
        "difficulty": _PROGRESSION_TO_DIFFICULTY.get(progression, "Medium"),
        "generation_stage_meta": {
            "stage_4_coverage_audit": True,
            "progression_label": progression,
            "coverage_item_type": item.item_type,
            "coverage_item_text": item.text,
            "source_type": item.source,
        },
    }


def build_profile_driven_questions(profile: JobIntelligenceProfile) -> list[dict[str, Any]]:
    """Pre-coverage-plan questions derived directly from the Job Intelligence Profile."""
    questions: list[dict[str, Any]] = []
    role = profile.job_title
    for idx, resp in enumerate(profile.responsibilities[:8]):
        progression = _PROGRESSION_LABELS[idx % len(_PROGRESSION_LABELS)]
        questions.append(
            {
                "category": "role_specific",
                "question": (
                    f"Describe how you would plan and execute {_shorten(resp)} as a {role}, "
                    f"including quality checks and stakeholder communication."
                ),
                "why_asked": "Profile-driven responsibility coverage from user job input.",
                "ideal_answer_points": [f"Covers {resp}", "Explains steps and checks", "Uses role-specific context"],
                "question_type": "responsibility",
                "skill_tag": role,
                "difficulty": _PROGRESSION_TO_DIFFICULTY.get(progression, "Medium"),
                "generation_stage_meta": {"progression_label": progression, "profile_driven": True},
            }
        )
    for idx, tool in enumerate(profile.tools_software[:6]):
        progression = _PROGRESSION_LABELS[(idx + 1) % len(_PROGRESSION_LABELS)]
        resp = profile.responsibilities[0] if profile.responsibilities else tool
        questions.append(
            {
                "category": "technical",
                "question": (
                    f"How would you use {tool} to support {_shorten(resp)} in this {role} role, "
                    f"and what validation would you run before sign-off?"
                ),
                "why_asked": "Profile-driven tool coverage from extracted job input.",
                "ideal_answer_points": [f"Uses {tool}", "Explains workflow", "Includes validation checks"],
                "question_type": "tool_usage",
                "skill_tag": tool,
                "difficulty": _PROGRESSION_TO_DIFFICULTY.get(progression, "Medium"),
                "generation_stage_meta": {"progression_label": progression, "profile_driven": True},
            }
        )
    if profile.company_profile or profile.company_products_services:
        focus = profile.company_products_services or profile.company_profile or profile.industry_domain
        questions.append(
            {
                "category": "company_specific",
                "question": (
                    f"How would you adapt your priorities as a {role} knowing the company focus is "
                    f"{_shorten(str(focus), 100)}?"
                ),
                "why_asked": "Profile-driven company-context coverage.",
                "ideal_answer_points": ["References company context", "Links to role deliverables"],
                "question_type": "company_context",
                "skill_tag": role,
                "generation_stage_meta": {"progression_label": "scenario", "profile_driven": True},
            }
        )
    for clue in profile.compliance_safety_ethics[:4]:
        questions.append(
            {
                "category": "role_specific",
                "question": (
                    f"What safety, ethics, or compliance checks would you apply for "
                    f"{_shorten(clue)} in this {role} role?"
                ),
                "why_asked": "Profile-driven compliance/safety coverage.",
                "ideal_answer_points": ["Names risks", "Explains controls", "Shows escalation judgment"],
                "question_type": "compliance",
                "skill_tag": role,
                "generation_stage_meta": {"progression_label": "advanced", "profile_driven": True},
            }
        )
    return questions


def build_missing_coverage_questions(
    profile: JobIntelligenceProfile,
    existing_questions: list[dict[str, Any]],
    *,
    max_add: int = 12,
) -> list[dict[str, Any]]:
    audit = audit_pack_coverage(profile, existing_questions)
    if not audit.missing_items:
        return []

    existing_blob = " ".join(_norm(q.get("question", "")) for q in existing_questions)
    added: list[dict[str, Any]] = []
    priority = sorted(
        audit.missing_items,
        key=lambda i: (0 if i.importance == "critical" else 1 if i.importance == "high" else 2, i.item_type),
    )
    for idx, item in enumerate(priority[:max_add]):
        progression = _PROGRESSION_LABELS[idx % len(_PROGRESSION_LABELS)]
        draft = _question_for_item(item, profile, progression)
        if _norm(draft["question"]) in _norm(existing_blob):
            continue
        added.append(draft)
        existing_blob += " " + _norm(draft["question"])
    return added


def apply_coverage_audit_and_fill(
    profile: JobIntelligenceProfile,
    questions: list[dict[str, Any]],
    *,
    finalize_fn,
    job: dict[str, Any],
    difficulty: str,
) -> tuple[list[dict[str, Any]], CoverageAuditResult]:
    """Run audit, append missing-item questions, finalize, and return exportable questions + audit."""
    added_raw = build_missing_coverage_questions(profile, questions)
    combined = list(questions)
    seen = {re.sub(r"\s+", " ", (q.get("question") or "").lower().strip()) for q in questions}
    for q in added_raw:
        key = re.sub(r"\s+", " ", (q.get("question") or "").lower().strip())
        if key in seen:
            continue
        seen.add(key)
        combined.append(q)

    finalized = [finalize_fn(q, job, difficulty, i) for i, q in enumerate(combined)]
    exportable = [q for q in finalized if not q.get("export_blocked")]
    audit = audit_pack_coverage(profile, exportable)
    audit.added_question_count = len(added_raw)
    return exportable, audit


def audit_to_dict(audit: CoverageAuditResult) -> dict[str, Any]:
    from app.agents.job_search.knowledge.source_ladder import _source_label

    data = asdict(audit)
    missing_dicts = []
    for i in audit.missing_items:
        row = asdict(i)
        row["item_id"] = getattr(i, "item_id", None)
        row["item_text"] = i.text
        row["source_type"] = i.source
        row["source_label"] = getattr(i, "source_label", None) or _source_label(i.source)
        row["action"] = "add_question"
        missing_dicts.append(row)
    data["missing_items"] = missing_dicts
    return data


def build_audit_items_for_profile(profile: JobIntelligenceProfile) -> list[dict[str, Any]]:
    from app.agents.job_search.knowledge.source_ladder import build_coverage_audit_items

    return build_coverage_audit_items(profile)
