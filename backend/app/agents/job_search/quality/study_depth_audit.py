from __future__ import annotations

from typing import Any

REQUIRED_STUDY_BLOCKS = [
    "what_this_question_tests",
    "beginner_explanation",
    "intermediate_explanation",
    "advanced_explanation",
    "key_terms",
    "step_by_step_method",
    "worked_example",
    "common_mistakes",
    "interview_traps",
    "mini_practice_task",
]

_BANNED_STUDY_TERMS = (
    "generic wording",
    "missing final verification",
    "benchmark check",
    "documentation review",
    "acceptance criteria",
)


def _word_count(s: str) -> int:
    return len((s or "").split())


def study_depth_score(study_material: dict[str, Any]) -> float:
    if not study_material:
        return 0.0
    completed = 0
    for k in REQUIRED_STUDY_BLOCKS:
        v = study_material.get(k)
        if isinstance(v, str) and v.strip():
            completed += 1
        elif isinstance(v, list) and len(v) > 0:
            completed += 1
    return round((completed / len(REQUIRED_STUDY_BLOCKS)) * 100, 1)


def validate_study_material(study_material: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    score = study_depth_score(study_material)
    if score < 80.0:  # at least 8/10 blocks
        failures.append("study_blocks_incomplete")

    if _word_count(study_material.get("beginner_explanation", "")) < 40:
        failures.append("weak_beginner_explanation")
    if _word_count(study_material.get("intermediate_explanation", "")) < 60:
        failures.append("weak_intermediate_explanation")
    if _word_count(study_material.get("advanced_explanation", "")) < 60:
        failures.append("weak_advanced_explanation")
    if _word_count(study_material.get("worked_example", "")) < 60:
        failures.append("weak_worked_example")
    if len(study_material.get("step_by_step_method", []) or []) < 4:
        failures.append("weak_step_by_step")
    if len(study_material.get("common_mistakes", []) or []) < 3:
        failures.append("weak_common_mistakes")
    if len(study_material.get("interview_traps", []) or []) < 2:
        failures.append("weak_interview_traps")
    if _word_count(study_material.get("mini_practice_task", "")) < 30:
        failures.append("weak_mini_practice_task")
    blob = " ".join(
        [str(study_material.get("worked_example", ""))]
        + [str(x) for x in (study_material.get("common_mistakes") or [])]
        + [str(x) for x in (study_material.get("troubleshooting_checklist") or [])]
    ).lower()
    if any(term in blob for term in _BANNED_STUDY_TERMS):
        failures.append("study_internal_qa_language")
    return failures
