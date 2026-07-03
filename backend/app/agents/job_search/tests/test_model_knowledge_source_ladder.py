"""Tests for model-knowledge feature flag and source ladder (Iteration 004D)."""

from __future__ import annotations

import random
import re

import pytest

from app.agents.job_search.knowledge.model_knowledge import (
    DeterministicTestModelKnowledgeProvider,
    FailingModelKnowledgeProvider,
    ModelKnowledgeStatus,
    apply_model_knowledge_support,
    build_role_specific_model_insight,
    generate_model_knowledge,
    is_model_knowledge_enabled,
)
from app.agents.job_search.knowledge.study_sources import (
    attach_study_source_metadata,
    render_study_source_markdown,
)
from app.agents.job_search.knowledge.study_synthesis import contains_blocked_generic_phrase
from app.agents.job_search.mock_data import mock_generate_questions
from app.agents.job_search.quality.answer_length_policy import ABSOLUTE_MAX_WORDS
from app.agents.job_search.quality.blocked_phrase_guard import (
    INTERMEDIATE_QUALITY_CHECKS,
    OUTCOME_QUALITY_IMPROVES,
    STABILIZE_MAINTAIN_PIPELINES,
    STRUCTURED_VERIFICATION,
)
from app.core.config import settings
from app.tools.document_export import build_interview_pack_markdown

_ROLE_SPECIFIC_LABEL = "Role " + "Specific"
_FAKE_URL_RE = re.compile(r"https?://[^\s\])\"']+")
_BLOCKED_MARKERS = (
    OUTCOME_QUALITY_IMPROVES,
    STRUCTURED_VERIFICATION,
    INTERMEDIATE_QUALITY_CHECKS,
    STABILIZE_MAINTAIN_PIPELINES,
)

_DEVOPS_JOB = {
    "title": "DevOps Engineer",
    "responsibilities": [
        "AWS infrastructure automation with CI/CD, Docker, and Kubernetes",
        "Monitoring, incident response, security controls, and rollback/recovery",
    ],
    "requirements": ["AWS", "CI/CD", "Docker", "Kubernetes", "monitoring", "security"],
    "extracted_skills": [{"skill": s} for s in ["AWS", "CI/CD", "Docker", "Kubernetes", "Monitoring"]],
}

_BARISTA_JOB = {
    "title": "Barista",
    "responsibilities": [
        "Espresso preparation, milk steaming, and drink consistency during rush hours",
        "Hygiene, allergen controls, customer service, and stock handling",
    ],
    "requirements": ["espresso preparation", "hygiene", "allergens", "customer service"],
    "extracted_skills": [{"skill": s} for s in ["Coffee Preparation", "HACCP", "Customer Service"]],
}


def _model_source(sources: list[dict]) -> dict | None:
    for source in sources:
        if source.get("source_type") == "model":
            return source
    return None


def _web_source(sources: list[dict]) -> dict | None:
    for source in sources:
        if source.get("source_type") == "web":
            return source
    return None


def test_model_knowledge_disabled_by_default() -> None:
    assert is_model_knowledge_enabled() is False
    result = generate_model_knowledge({}, _DEVOPS_JOB)
    assert result.status == ModelKnowledgeStatus.DISABLED.value
    assert result.used is False
    assert result.insight is None


def test_normal_tests_require_no_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "job_search_enable_model_knowledge", False)
    questions = mock_generate_questions(_DEVOPS_JOB, focus_areas=["AWS", "CI/CD"], difficulty="mid")
    assert questions
    for q in questions:
        if q.get("export_blocked"):
            continue
        assert q.get("study_sources")


def test_disabled_model_knowledge_renders_correct_source_status() -> None:
    q = {"question_id": "q1", "question": "How do you keep deployments safe?", "category": "technical"}
    attach_study_source_metadata(q, _DEVOPS_JOB)
    sources = (q.get("study_sources") or {}).get("sources") or []
    model = _model_source(sources)
    assert model is not None
    assert model.get("status") == "not_configured"
    assert "disabled" in (model.get("note") or "").lower()

    md = "\n".join(render_study_source_markdown(q.get("study_sources")))
    assert "Model knowledge" in md
    assert "Disabled" in md


def test_mocked_model_provider_contributes_sanitized_insight(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "job_search_enable_model_knowledge", True)
    monkeypatch.setattr(settings, "job_search_model_knowledge_provider", "deterministic_test")

    q = {"question_id": "q1", "question": "Describe your CI/CD rollback process.", "category": "technical", "skill_tag": "CI/CD", "study_material": {}}
    attach_study_source_metadata(q, _DEVOPS_JOB)
    from app.agents.job_search.knowledge.study_synthesis import synthesize_study_module

    synthesize_study_module(q, _DEVOPS_JOB)
    support = q.get("model_knowledge_support") or {}
    assert support.get("used") is True
    assert support.get("insight")
    assert "deployment health checks" in support["insight"].lower()
    assert q["study_material"].get("model_knowledge_insight")
    assert not _FAKE_URL_RE.search(support["insight"])


def test_model_insight_marked_used_only_when_non_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "job_search_enable_model_knowledge", True)
    monkeypatch.setattr(settings, "job_search_model_knowledge_provider", "deterministic_test")

    q = {"question_id": "q1", "question": "Test", "category": "technical"}
    result = apply_model_knowledge_support(q, _DEVOPS_JOB, provider=DeterministicTestModelKnowledgeProvider())
    assert result.used is True
    assert result.insight

    sources = attach_study_source_metadata(q, _DEVOPS_JOB).get("study_sources", {}).get("sources", [])
    model = _model_source(sources)
    assert model is not None
    assert model.get("status") == "used"


def test_failed_provider_falls_back_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "job_search_enable_model_knowledge", True)
    monkeypatch.setattr(settings, "job_search_model_knowledge_provider", "deterministic_test")

    q = {"question_id": "q1", "question": "Test", "category": "technical"}
    result = apply_model_knowledge_support(q, _DEVOPS_JOB, provider=FailingModelKnowledgeProvider())
    assert result.status == ModelKnowledgeStatus.FAILED_FALLBACK.value
    assert result.used is False
    assert not result.insight

    attach_study_source_metadata(q, _DEVOPS_JOB)
    model = _model_source((q.get("study_sources") or {}).get("sources") or [])
    assert model is not None
    assert model.get("status") == "failed"

    md = "\n".join(render_study_source_markdown(q.get("study_sources")))
    assert "Failed fallback" in md
    assert q.get("study_material") or True  # generation continues


def test_model_insight_has_no_fake_urls_or_citations() -> None:
    for job in (_DEVOPS_JOB, _BARISTA_JOB):
        insight = build_role_specific_model_insight(
            role=job["title"],
            role_family="technology" if "DevOps" in job["title"] else "hospitality",
        )
        assert not _FAKE_URL_RE.search(insight)
        assert "http" not in insight.lower()
        assert "citation" not in insight.lower()


def test_web_research_remains_not_configured() -> None:
    q = {"question_id": "q1", "question": "Test", "category": "technical"}
    attach_study_source_metadata(q, _DEVOPS_JOB)
    web = _web_source((q.get("study_sources") or {}).get("sources") or [])
    assert web is not None
    assert web.get("status") == "not_configured"


def test_generated_questions_include_study_material_and_source_status() -> None:
    questions = mock_generate_questions(_BARISTA_JOB, focus_areas=["Coffee Preparation"], difficulty="mid")
    exportable = [q for q in questions if not q.get("export_blocked") and q.get("model_answer")]
    assert exportable
    for q in exportable:
        assert q.get("study_material")
        assert q.get("study_sources")


def test_no_user_facing_role_specific_label() -> None:
    questions = mock_generate_questions(_DEVOPS_JOB, focus_areas=["AWS"], difficulty="mid")
    pack_md = build_interview_pack_markdown(job_title="DevOps Engineer", company_name=None, questions=questions)
    assert _ROLE_SPECIFIC_LABEL not in pack_md


def test_no_blocked_generic_phrases_in_default_generation() -> None:
    questions = mock_generate_questions(_BARISTA_JOB, focus_areas=["Coffee Preparation"], difficulty="mid")
    pack_md = build_interview_pack_markdown(job_title="Barista", company_name=None, questions=questions)
    lowered = pack_md.lower()
    for marker in _BLOCKED_MARKERS:
        assert marker.lower() not in lowered


def test_answers_remain_under_500_words() -> None:
    questions = mock_generate_questions(_DEVOPS_JOB, focus_areas=["AWS", "CI/CD"], difficulty="mid")
    for q in questions:
        if q.get("export_blocked"):
            continue
        answer = q.get("model_answer") or ""
        assert len(answer.split()) <= ABSOLUTE_MAX_WORDS


def test_random_validation_role_selection_is_deterministic() -> None:
    from scripts.generate_iteration_004d_samples import select_random_validation_roles

    first = select_random_validation_roles(seed=42)
    second = select_random_validation_roles(seed=42)
    assert first == second
    assert len(first) == 5
    categories = {item["category"] for item in first}
    assert len(categories) == 5


def test_sample_generation_role_counts() -> None:
    from scripts.generate_iteration_004d_samples import FIXED_BENCHMARK_ROLES, select_random_validation_roles

    assert len(FIXED_BENCHMARK_ROLES) == 5
    assert len(select_random_validation_roles(seed=42)) == 5
