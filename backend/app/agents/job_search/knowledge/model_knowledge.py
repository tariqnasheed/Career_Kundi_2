"""Model-knowledge study synthesis behind a feature flag (Iteration 004D).

Disabled by default. No fake URLs or citations. Falls back to local deterministic
and document-library material when disabled or on provider failure.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from app.agents.job_search.knowledge.source_sanitizer import sanitize_knowledge_text
from app.agents.job_search.knowledge.study_synthesis import infer_role_family
from app.core.config import settings

_URL_RE = re.compile(r"https?://[^\s\])\"']+", re.I)
_CITATION_RE = re.compile(r"\[[^\]]*\]\([^)]+\)|\bcitation\b|\bsource:\s*http", re.I)


class ModelKnowledgeStatus(str, Enum):
    NOT_CONFIGURED = "not_configured"
    DISABLED = "disabled"
    AVAILABLE_NOT_USED = "available_not_used"
    USED = "used"
    FAILED_FALLBACK = "failed_fallback"


@dataclass
class ModelKnowledgeResult:
    status: str
    used: bool
    insight: str | None
    provider_name: str | None
    reason: str
    warnings: list[str] = field(default_factory=list)


_ROLE_FAMILY_FOCUS: dict[str, tuple[str, str]] = {
    "technology": (
        "deployment health checks, rollback criteria, monitoring alerts, and pipeline gates",
        "how you keep releases safe under pressure",
    ),
    "healthcare": (
        "allergy checks, contraindications, interaction review, and counselling points",
        "how you protect patient safety when time is tight",
    ),
    "hospitality": (
        "grind and dose control, extraction time, milk texture, and allergen handling",
        "how you keep drink quality and hygiene consistent during rush periods",
    ),
    "data": (
        "SQL validation, null checks, KPI definitions, and dashboard filter logic",
        "how you keep stakeholder numbers trustworthy",
    ),
    "electrical": (
        "load assumptions, cable derating, protective-device coordination, and inspection records",
        "how you keep installations safe and compliant on site",
    ),
    "general": (
        "the matched workflow points, quality checks, practical examples, and interview-ready explanation",
        "how you explain your method clearly under interview pressure",
    ),
}


def _sanitize_insight(text: str, *, role_title: str, skill: str | None) -> str:
    cleaned = sanitize_knowledge_text(text, role_title=role_title, skill=skill)
    cleaned = _URL_RE.sub("", cleaned)
    cleaned = _CITATION_RE.sub("", cleaned)
    return cleaned.strip()


def build_role_specific_model_insight(*, role: str, role_family: str, skill_tag: str | None = None) -> str:
    """Deterministic role-family insight for tests and the deterministic_test provider."""
    focus, practise = _ROLE_FAMILY_FOCUS.get(role_family, _ROLE_FAMILY_FOCUS["general"])
    raw = (
        f"The model-knowledge layer reinforces this {role} question by focusing on {focus}. "
        f"Use this to practise explaining {practise}."
    )
    return _sanitize_insight(raw, role_title=role, skill=skill_tag)


class ModelKnowledgeProvider(Protocol):
    def generate(self, question: dict[str, Any], job: dict[str, Any]) -> ModelKnowledgeResult: ...


class DeterministicTestModelKnowledgeProvider:
    """Test-only deterministic provider — no API calls."""

    provider_name = "deterministic_test"

    def generate(self, question: dict[str, Any], job: dict[str, Any]) -> ModelKnowledgeResult:
        role = job.get("title") or "this role"
        family = infer_role_family(job)
        insight = build_role_specific_model_insight(
            role=role,
            role_family=family,
            skill_tag=question.get("skill_tag"),
        )
        if not insight:
            return ModelKnowledgeResult(
                status=ModelKnowledgeStatus.AVAILABLE_NOT_USED.value,
                used=False,
                insight=None,
                provider_name=self.provider_name,
                reason="Deterministic test provider returned empty insight.",
            )
        return ModelKnowledgeResult(
            status=ModelKnowledgeStatus.USED.value,
            used=True,
            insight=insight,
            provider_name=self.provider_name,
            reason="Deterministic test provider supplied role-specific study insight.",
        )


class FailingModelKnowledgeProvider:
    """Test double that always fails — verifies safe fallback."""

    provider_name = "failing_test"

    def generate(self, question: dict[str, Any], job: dict[str, Any]) -> ModelKnowledgeResult:
        return ModelKnowledgeResult(
            status=ModelKnowledgeStatus.FAILED_FALLBACK.value,
            used=False,
            insight=None,
            provider_name=self.provider_name,
            reason="Provider raised a simulated failure.",
            warnings=["Simulated provider failure for fallback testing."],
        )


def is_model_knowledge_enabled() -> bool:
    return bool(settings.job_search_enable_model_knowledge)


def resolve_model_knowledge_provider(
    *,
    override: ModelKnowledgeProvider | None = None,
) -> ModelKnowledgeProvider | None:
    if override is not None:
        return override
    if not is_model_knowledge_enabled():
        return None
    provider_key = (settings.job_search_model_knowledge_provider or "disabled").strip().lower()
    if provider_key in {"disabled", ""}:
        return None
    if provider_key == "deterministic_test":
        return DeterministicTestModelKnowledgeProvider()
    return None


def generate_model_knowledge(
    question: dict[str, Any],
    job: dict[str, Any],
    *,
    provider: ModelKnowledgeProvider | None = None,
) -> ModelKnowledgeResult:
    """Attempt model-knowledge synthesis when the feature flag and provider allow it."""
    if not is_model_knowledge_enabled():
        return ModelKnowledgeResult(
            status=ModelKnowledgeStatus.DISABLED.value,
            used=False,
            insight=None,
            provider_name=None,
            reason="Model-knowledge synthesis is disabled by feature flag.",
        )

    provider_key = (settings.job_search_model_knowledge_provider or "disabled").strip().lower()
    if provider_key in {"disabled", ""}:
        return ModelKnowledgeResult(
            status=ModelKnowledgeStatus.NOT_CONFIGURED.value,
            used=False,
            insight=None,
            provider_name=None,
            reason="Model-knowledge provider is set to disabled.",
        )

    resolved = resolve_model_knowledge_provider(override=provider)
    if resolved is None:
        if provider_key == "gemini":
            return ModelKnowledgeResult(
                status=ModelKnowledgeStatus.FAILED_FALLBACK.value,
                used=False,
                insight=None,
                provider_name="gemini",
                reason="Gemini model-knowledge provider is not enabled for study modules in this iteration.",
                warnings=["Use deterministic_test provider for local validation."],
            )
        return ModelKnowledgeResult(
            status=ModelKnowledgeStatus.NOT_CONFIGURED.value,
            used=False,
            insight=None,
            provider_name=provider_key,
            reason=f"Unknown model-knowledge provider: {provider_key}.",
        )

    try:
        result = resolved.generate(question, job)
    except Exception as exc:
        return ModelKnowledgeResult(
            status=ModelKnowledgeStatus.FAILED_FALLBACK.value,
            used=False,
            insight=None,
            provider_name=getattr(resolved, "provider_name", provider_key),
            reason=f"Model-knowledge synthesis failed: {exc}",
            warnings=[str(exc)],
        )

    if result.insight:
        result.insight = _sanitize_insight(
            result.insight,
            role_title=job.get("title") or "",
            skill=question.get("skill_tag"),
        )
        if not result.insight:
            return ModelKnowledgeResult(
                status=ModelKnowledgeStatus.FAILED_FALLBACK.value,
                used=False,
                insight=None,
                provider_name=result.provider_name,
                reason="Sanitized model insight was empty.",
                warnings=["Insight removed during sanitization."],
            )
        if _URL_RE.search(result.insight) or _CITATION_RE.search(result.insight):
            return ModelKnowledgeResult(
                status=ModelKnowledgeStatus.FAILED_FALLBACK.value,
                used=False,
                insight=None,
                provider_name=result.provider_name,
                reason="Model insight contained disallowed URL or citation patterns.",
            )
        result.used = True
        result.status = ModelKnowledgeStatus.USED.value
    elif result.status == ModelKnowledgeStatus.USED.value:
        result.used = False
        result.status = ModelKnowledgeStatus.AVAILABLE_NOT_USED.value
    return result


def apply_model_knowledge_support(
    question: dict[str, Any],
    job: dict[str, Any],
    *,
    provider: ModelKnowledgeProvider | None = None,
) -> ModelKnowledgeResult:
    """Attach model-knowledge support metadata to a question when insight is available."""
    result = generate_model_knowledge(question, job, provider=provider)
    question["model_knowledge_support"] = {
        "status": result.status,
        "used": result.used,
        "insight": result.insight,
        "provider_name": result.provider_name,
        "reason": result.reason,
        "warnings": list(result.warnings),
    }
    return result


def model_knowledge_study_source_status(result: ModelKnowledgeResult) -> tuple[str, str]:
    """Map model-knowledge result to study-source status and note."""
    status = result.status
    if status == ModelKnowledgeStatus.DISABLED.value:
        return "not_configured", "Disabled — Model-knowledge synthesis is disabled by feature flag."
    if status == ModelKnowledgeStatus.NOT_CONFIGURED.value:
        return "not_configured", "Model-knowledge retrieval is not configured."
    if status == ModelKnowledgeStatus.USED.value and result.used and result.insight:
        return "used", "Model-knowledge layer supplied a concise study insight for this question."
    if status == ModelKnowledgeStatus.FAILED_FALLBACK.value:
        return (
            "failed",
            "Model-knowledge synthesis failed, so the module used local deterministic and document-library material.",
        )
    if status == ModelKnowledgeStatus.AVAILABLE_NOT_USED.value:
        return "available_not_used", result.reason or "Model knowledge available but not used for this question."
    return "not_configured", result.reason or "Model-knowledge retrieval is not configured."
