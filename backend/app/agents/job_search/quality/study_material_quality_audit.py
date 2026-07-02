from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from app.agents.job_search.knowledge.question_intent import detect_question_intent
from app.agents.job_search.quality.study_material_phrase_audit import (
    study_banned_phrase_count,
    study_placeholder_count,
)

MIN_COMPONENTS = 3
MIN_STUDY_CHARS = 200
DUPLICATE_SIMILARITY_THRESHOLD = 0.82


def _study_blob(study: dict[str, Any]) -> str:
    parts: list[str] = []
    for key, value in study.items():
        if key == "quality_audit":
            continue
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            parts.extend(str(v) for v in value if v)
    return " ".join(parts)


def _count_learning_components(study: dict[str, Any]) -> int:
    components = 0
    if any(study.get(k) for k in ("overview", "what_this_question_tests", "beginner_explanation", "intermediate_explanation")):
        components += 1
    if study.get("step_by_step_method") or study.get("step_by_step_breakdown"):
        components += 1
    if study.get("common_mistakes"):
        components += 1
    if study.get("worked_example") or study.get("practical_example"):
        components += 1
    if study.get("interview_traps") or study.get("how_to_answer_better") or study.get("mini_practice_task"):
        components += 1
    if study.get("formula_or_framework") or study.get("troubleshooting_checklist"):
        components += 1
    if study.get("key_terms") or study.get("definitions"):
        components += 1
    return components


def _question_specificity_score(question: dict[str, Any], study: dict[str, Any]) -> float:
    blob = _study_blob(study).lower()
    skill = str(question.get("mapped_skill") or question.get("skill_tag") or "").lower()
    qtext = str(question.get("question") or "").lower()
    if skill and skill in blob:
        return 100.0
    tokens = [t for t in qtext.split() if len(t) > 4]
    hits = sum(1 for t in tokens[:8] if t in blob)
    if not tokens:
        return 0.0
    return round(min(100.0, (hits / min(len(tokens), 4)) * 100), 1)


def _format_issue(role: str, skill: str, question: str, reason: str) -> str:
    skill_bit = skill or "General"
    qbit = question[:90] if question else "n/a"
    return f'{role} / {skill_bit}: study material for "{qbit}": {reason}'


def audit_study_material(
    study: dict[str, Any],
    question: dict[str, Any],
    *,
    role: str,
    peer_studies: list[str] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    skill = str(question.get("mapped_skill") or question.get("skill_tag") or "General")
    qtext = str(question.get("question") or "")
    intent = detect_question_intent(qtext, question.get("question_type"), category=question.get("category"))

    if not study:
        errors.append(_format_issue(role, skill, qtext, "study material missing (expected structured module, actual none)"))
        return {
            "passed": False,
            "score": 0.0,
            "errors": errors,
            "warnings": warnings,
            "component_count": 0,
            "generic_phrase_count": 0,
            "question_specificity_score": 0.0,
            "duplicate_similarity_score": 0.0,
            "intent": intent,
        }

    blob = _study_blob(study)
    component_count = _count_learning_components(study)
    specificity = _question_specificity_score(question, study)
    generic_count = study_banned_phrase_count(blob)
    placeholder_count = study_placeholder_count(blob)

    if component_count < MIN_COMPONENTS:
        errors.append(
            _format_issue(
                role,
                skill,
                qtext,
                f"has only {component_count} learning components; expected at least {MIN_COMPONENTS}",
            )
        )
    if len(blob) < MIN_STUDY_CHARS:
        errors.append(
            _format_issue(
                role,
                skill,
                qtext,
                f"module too short (expected >= {MIN_STUDY_CHARS} chars, actual {len(blob)})",
            )
        )
    if specificity < 50.0:
        errors.append(
            _format_issue(
                role,
                skill,
                qtext,
                f"not question-specific enough (expected >= 50, actual {specificity})",
            )
        )
    if generic_count:
        errors.append(
            _format_issue(
                role,
                skill,
                qtext,
                f"contains banned generic study phrases (expected 0, actual {generic_count})",
            )
        )
    if placeholder_count:
        errors.append(
            _format_issue(
                role,
                skill,
                qtext,
                f"contains placeholder text (expected 0, actual {placeholder_count})",
            )
        )

    duplicate_similarity = 0.0
    if peer_studies:
        for peer in peer_studies:
            if not peer:
                continue
            ratio = SequenceMatcher(None, blob.lower(), peer.lower()).ratio()
            duplicate_similarity = max(duplicate_similarity, ratio)
        if duplicate_similarity >= DUPLICATE_SIMILARITY_THRESHOLD:
            errors.append(
                _format_issue(
                    role,
                    skill,
                    qtext,
                    f"duplicate study module across unrelated roles "
                    f"(similarity {duplicate_similarity:.2f} >= {DUPLICATE_SIMILARITY_THRESHOLD})",
                )
            )

    passed = not errors
    penalty = (len(errors) * 15) + (len(warnings) * 4) + generic_count * 5
    score = max(0.0, round(100.0 - penalty, 1))
    return {
        "passed": passed,
        "score": score,
        "errors": errors,
        "warnings": warnings,
        "component_count": component_count,
        "generic_phrase_count": generic_count,
        "question_specificity_score": specificity,
        "duplicate_similarity_score": round(duplicate_similarity, 3),
        "intent": intent,
    }
