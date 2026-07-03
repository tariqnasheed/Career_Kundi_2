from __future__ import annotations

import json
from pathlib import Path

from app.agents.job_search.knowledge.content_engine import _load_knowledge, get_skill_knowledge
from app.agents.job_search.knowledge.source_sanitizer import (
    knowledge_text_is_clean,
    sanitize_knowledge_text,
)
from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.blocked_phrase_guard import (
    DOCUMENTED_CONTROL_POINTS,
    INTERMEDIATE_QUALITY_CHECKS,
    OUTCOME_QUALITY_IMPROVES,
    STRUCTURED_VERIFICATION,
    USING_DOC_PROCEDURES,
)
from app.agents.job_search.quality.surface_text_normalize import normalize_surface_text
from app.services.role_pack_library import build_role_overview
from app.tools.document_export import build_interview_pack_markdown

KNOWLEDGE_PATH = Path(__file__).resolve().parents[1] / "knowledge" / "skill_knowledge.json"

_ROLE_SPECIFIC_LABEL = "Role " + "Specific"

_BLOCKED_MARKERS = (
    OUTCOME_QUALITY_IMPROVES,
    STRUCTURED_VERIFICATION,
    INTERMEDIATE_QUALITY_CHECKS,
    USING_DOC_PROCEDURES,
    DOCUMENTED_CONTROL_POINTS,
)

_JOINED_ARTIFACTS = (
    "usingdocumented",
    "documentedthe",
    "assumptionsare",
    "beforeproceeding",
)

_ROLE_SNAPSHOTS = [
    {
        "title": "DevOps Engineer",
        "primary_skill": "AWS",
        "extracted_skills": ["AWS", "CI/CD", "Docker", "Kubernetes", "Monitoring"],
        "responsibilities": ["AWS infrastructure automation with CI/CD and monitoring"],
        "requirements": ["AWS", "CI/CD", "monitoring"],
    },
    {
        "title": "Clinical Pharmacist",
        "primary_skill": "Pharmacology",
        "extracted_skills": ["Pharmacology", "Medication Review"],
        "responsibilities": ["Medication review and patient counselling"],
        "requirements": ["medication review", "patient counselling"],
    },
]


def test_sanitizer_rewrites_blocked_phrases() -> None:
    dirty = (
        "Outcome quality improves when assumptions are explicit and testable. "
        "We used structured verification, documented the control points, and "
        f"{USING_DOC_PROCEDURES}."
    )
    cleaned = sanitize_knowledge_text(
        dirty,
        role_title="DevOps Engineer",
        skill="AWS",
    )
    assert knowledge_text_is_clean(cleaned)
    for marker in _BLOCKED_MARKERS:
        assert marker.lower() not in cleaned.lower()


def test_sanitizer_fixes_joined_word_artifacts() -> None:
    dirty = (
        "Apply AWS usingdocumented proceduresand intermediatequality checks "
        "beforeproceeding because assumptionsare explicit and documentedthe control points."
    )
    cleaned = sanitize_knowledge_text(
        dirty,
        role_title="Data Analyst",
        skill="SQL",
    )
    lowered = cleaned.lower()
    for artifact in _JOINED_ARTIFACTS:
        assert artifact not in lowered
    assert knowledge_text_is_clean(cleaned)


def test_sanitizer_preserves_meaningful_skill_terms() -> None:
    cleaned = sanitize_knowledge_text(
        "Use SQL joins, null checks, and KPI definitions when validating dashboard filter logic.",
        role_title="Data Analyst",
        skill="SQL",
    )
    assert "SQL" in cleaned
    assert "KPI" in cleaned
    assert "null checks" in cleaned.lower()


def test_runtime_knowledge_load_is_sanitized() -> None:
    _load_knowledge.cache_clear()
    payload = _load_knowledge()
    blob = json.dumps(payload)
    assert OUTCOME_QUALITY_IMPROVES.lower() not in blob.lower()
    assert STRUCTURED_VERIFICATION.lower() not in blob.lower()
    assert INTERMEDIATE_QUALITY_CHECKS.lower() not in blob.lower()

    aws = get_skill_knowledge("AWS")
    expert_blob = json.dumps(aws)
    assert STRUCTURED_VERIFICATION.lower() not in expert_blob.lower()


def test_generated_samples_have_no_blocked_phrases_or_role_specific() -> None:
    for snapshot in _ROLE_SNAPSHOTS:
        job = {
            "title": snapshot["title"],
            "responsibilities": snapshot["responsibilities"],
            "requirements": snapshot["requirements"],
            "extracted_skills": [{"skill": s} for s in snapshot["extracted_skills"]],
        }
        questions = mock_generate_questions(job, focus_areas=[snapshot["primary_skill"]], difficulty="mid")
        pack_md = build_interview_pack_markdown(
            job_title=snapshot["title"],
            company_name=None,
            questions=questions,
            role_overview=build_role_overview(snapshot["title"], job),
        )
        lowered = pack_md.lower()
        for marker in _BLOCKED_MARKERS:
            assert marker.lower() not in lowered
        assert _ROLE_SPECIFIC_LABEL not in pack_md


def test_raw_skill_knowledge_file_may_still_contain_legacy_phrases() -> None:
    """Document deferred full regeneration: on-disk JSON may be stale; runtime load must be clean."""
    if not KNOWLEDGE_PATH.is_file():
        return
    raw = KNOWLEDGE_PATH.read_text(encoding="utf-8").lower()
    raw_has_blocked = any(marker.lower() in raw for marker in _BLOCKED_MARKERS)
    _load_knowledge.cache_clear()
    runtime_blob = json.dumps(_load_knowledge()).lower()
    runtime_clean = all(marker.lower() not in runtime_blob for marker in _BLOCKED_MARKERS)
    assert runtime_clean
    if raw_has_blocked:
        assert normalize_surface_text(raw) != runtime_blob
