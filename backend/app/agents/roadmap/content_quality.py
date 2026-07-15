"""Helpers that reject schema-valid but empty/weak Ollama study/practice payloads."""

from __future__ import annotations

from typing import Any

from app.agents.roadmap import mock_data

_USELESS_OVERVIEW_MARKERS = (
    "no relevant material",
    "no matching material",
    "unfortunately, no",
    "cannot create a study",
    "could not find",
    "not enough context",
    "no material was found",
    "i cannot",
    "i'm unable",
    "as an ai",
)


def _nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _nonempty_str_list(value: Any, *, min_items: int = 1) -> bool:
    if not isinstance(value, list):
        return False
    items = [str(x).strip() for x in value if str(x).strip()]
    return len(items) >= min_items


def _is_useful_overview(value: Any) -> bool:
    if not _nonempty_str(value):
        return False
    text = str(value).strip().lower()
    if len(text) < 40:
        return False
    return not any(marker in text for marker in _USELESS_OVERVIEW_MARKERS)


def is_useful_study_material(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    return _is_useful_overview(value.get("overview")) and _nonempty_str_list(
        value.get("key_concepts"), min_items=1
    )


def is_useful_practice_activities(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    return (
        _nonempty_str_list(value.get("exercises"), min_items=1)
        and _nonempty_str(value.get("project_idea"))
        and _nonempty_str_list(value.get("self_assessment_questions"), min_items=1)
    )


def normalize_study_material(
    value: Any,
    skill_name: str,
    target_role: str,
    *,
    source_sentence: str | None = None,
    citation_marker: int | None = None,
) -> dict[str, Any]:
    """
    Merge LLM output with deterministic useful content when fields are blank
    or the model returns a refusal / empty-context apology.

    Empty dicts / empty strings from Ollama JSON fallback are replaced — they
    must never persist as blank cards for active skills.
    """
    fallback = mock_data.build_study_overview(
        skill_name,
        target_role,
        source_sentence=source_sentence,
        citation_marker=citation_marker,
    )
    if not isinstance(value, dict):
        return fallback

    overview = value.get("overview")
    if not _is_useful_overview(overview):
        overview = fallback["overview"]

    concepts = value.get("key_concepts")
    if not _nonempty_str_list(concepts, min_items=1):
        concepts = fallback["key_concepts"]
    else:
        concepts = [str(c).strip() for c in concepts if str(c).strip()]
        # Pad to at least 4 useful concepts when the model under-delivers.
        for extra in fallback["key_concepts"]:
            if len(concepts) >= 4:
                break
            if extra not in concepts:
                concepts.append(extra)

    reading = value.get("estimated_reading_time_minutes")
    if not isinstance(reading, (int, float)) or reading <= 0:
        reading = fallback.get("estimated_reading_time_minutes")

    return {
        "overview": str(overview).strip(),
        "key_concepts": concepts,
        "estimated_reading_time_minutes": reading,
    }


def normalize_practice_activities(
    value: Any,
    skill_name: str,
    target_role: str,
    siblings: list[str],
) -> dict[str, Any]:
    fallback = mock_data.build_practice_activities(skill_name, target_role, siblings)
    if not isinstance(value, dict):
        return fallback

    exercises = value.get("exercises")
    if not _nonempty_str_list(exercises, min_items=1):
        exercises = fallback["exercises"]
    else:
        exercises = [str(e).strip() for e in exercises if str(e).strip()]
        for extra in fallback["exercises"]:
            if len(exercises) >= 4:
                break
            if extra not in exercises:
                exercises.append(extra)

    project_idea = value.get("project_idea")
    if not _nonempty_str(project_idea):
        project_idea = fallback["project_idea"]

    questions = value.get("self_assessment_questions")
    if not _nonempty_str_list(questions, min_items=1):
        questions = fallback["self_assessment_questions"]
    else:
        questions = [str(q).strip() for q in questions if str(q).strip()]
        for extra in fallback["self_assessment_questions"]:
            if len(questions) >= 5:
                break
            if extra not in questions:
                questions.append(extra)

    return {
        "exercises": exercises,
        "project_idea": str(project_idea).strip(),
        "self_assessment_questions": questions,
    }
