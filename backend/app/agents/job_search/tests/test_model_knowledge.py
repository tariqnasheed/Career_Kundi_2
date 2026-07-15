"""Model-knowledge provider option tests after Ollama migration."""

from __future__ import annotations

from app.agents.job_search.knowledge.model_knowledge import generate_model_knowledge
from app.core.config import settings


def test_ollama_model_knowledge_falls_back_until_wired(monkeypatch):
    monkeypatch.setattr(settings, "job_search_enable_model_knowledge", True)
    monkeypatch.setattr(settings, "job_search_model_knowledge_provider", "ollama")
    result = generate_model_knowledge(
        {"skill_tag": "python"},
        {"title": "Software Engineer"},
    )
    assert result.used is False
    assert result.provider_name == "ollama"
    assert result.status == "failed_fallback"


def test_deprecated_gemini_model_knowledge_name(monkeypatch):
    monkeypatch.setattr(settings, "job_search_enable_model_knowledge", True)
    # Bypass Settings Literal by setting attribute directly for legacy path.
    monkeypatch.setattr(settings, "job_search_model_knowledge_provider", "gemini")
    result = generate_model_knowledge(
        {"skill_tag": "python"},
        {"title": "Software Engineer"},
    )
    assert result.used is False
    assert "deprecated" in result.reason.lower() or "not active" in result.reason.lower()
