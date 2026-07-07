"""Deterministic obligation coverage audit for answers and study modules (004E-E2.3 D)."""

from __future__ import annotations

import re
from typing import Any

from app.agents.job_search.knowledge.question_obligations import (
    MAJOR_OBLIGATIONS,
    MODIFIER_OBLIGATIONS,
    Obligation,
    QuestionObligationProfile,
    get_question_obligation_profile,
    is_pure_motivation_profile,
    question_in_obligation_audit_scope,
)

# --- Coverage signals (bounded, obligation-specific) ---------------------------

_MOTIVATION_ANSWER_MARKERS = (
    "interested in this",
    "interested in the",
    "interested in",
    "motivated by",
    "attracts me",
    "attracted to",
    "drawn to",
    "why i want",
    "why i am applying",
    "posting centres",
    "posting centers",
    "fit for",
    "want to contribute",
    "want to join",
    "want to work there",
    "looking at",
    "excited about",
    "appeal of",
    "genuinely interests",
    "quote one responsibility",
    "posting attracts",
)
_COMPANY_ANSWER_MARKERS = (
    "what i know about",
    "research on",
    "researched",
    "looked at",
    "company's",
    "organisation's",
    "organization's",
    "their work in",
    "want to work there",
    "mission",
    "values",
)
_STRENGTHS_ANSWER_MARKERS = (
    "strength",
    "strong at",
    "good at",
    "capable",
    "experienced in",
    "bring",
    "skills listed",
    "structured habits",
)
_CONTRIBUTION_ANSWER_MARKERS = (
    "contribute",
    "add value",
    "help deliver",
    "help the team",
    "from week one",
    "from the first month",
    "hope to",
    "ready to learn",
)
_TECH_METHOD_WEAK = (
    "structured approach",
    "best practices",
    "industry standards",
    "relevant standards",
    "follow standards",
    "use a structured",
)
_TECH_PROCEDURE_DOMINANCE = (
    "confirm safe isolation",
    "establish the connected load",
    "demand factor",
    "design current",
    "pipeline gates",
    "rollback criteria",
    "index seek",
    "execution plan",
    "isolation records",
    "step-by-step",
    "i would start by",
    "then i would",
    "before closing the task",
)
_SCENARIO_ANSWER_MARKERS = (
    "constraint",
    "trade-off",
    "trade off",
    "prioriti",
    "escalat",
    "if ",
    "when ",
    "risk",
    "conflict",
    "deadline",
    "under pressure",
)
_METRIC_WEAK = (
    "relevant metric",
    "the metric",
    "monitor the metric",
    "track metrics",
)
_METRIC_STRONG = (
    "mttr",
    "kpi",
    "failure rate",
    "runtime",
    "logical reads",
    "freshness",
    "error rate",
    "reduced",
    "within sla",
    "percent",
    "%",
    "minutes",
    "seconds",
    "hours",
    "query runtime",
    "rollback time",
    "alarm coverage",
)
_STANDARD_WEAK = (
    "follow standards",
    "relevant standards",
    "applicable standards",
    "industry standards",
    "governing standard",
)
_FAILURE_WEAK = (
    "consider risks",
    "think about risks",
    "risk aware",
)
_FAILURE_STRONG = (
    "failure mode",
    "can go wrong",
    "common mistake",
    "mitigat",
    "detect",
    "recover",
    "prevent",
    "avoid",
    "escalat",
)


def _blob(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).lower().strip()


def _has_any(blob: str, markers: tuple[str, ...]) -> bool:
    return any(m in blob for m in markers)


def _missing_obligations(answer: str, profile: QuestionObligationProfile) -> list[str]:
    blob = _blob(answer)
    missing: list[str] = []
    obs = set(profile.obligations)

    if Obligation.MOTIVATION_FIT.value in obs and not _has_any(blob, _MOTIVATION_ANSWER_MARKERS):
        missing.append(Obligation.MOTIVATION_FIT.value)
    if Obligation.COMPANY_FIT.value in obs and not _has_any(blob, _COMPANY_ANSWER_MARKERS):
        missing.append(Obligation.COMPANY_FIT.value)
    if Obligation.STRENGTHS.value in obs and not _has_any(blob, _STRENGTHS_ANSWER_MARKERS):
        missing.append(Obligation.STRENGTHS.value)
    if Obligation.CONTRIBUTION.value in obs and not _has_any(blob, _CONTRIBUTION_ANSWER_MARKERS):
        missing.append(Obligation.CONTRIBUTION.value)
    if Obligation.SCENARIO_REASONING.value in obs and not _has_any(blob, _SCENARIO_ANSWER_MARKERS):
        missing.append(Obligation.SCENARIO_REASONING.value)

    if Obligation.TECHNICAL_METHOD.value in obs:
        has_workflow = _has_any(blob, _TECH_PROCEDURE_DOMINANCE) or (
            blob.count("i would ") >= 2 and len(blob.split()) >= 40
        )
        only_weak = _has_any(blob, _TECH_METHOD_WEAK) and not has_workflow
        if only_weak or not has_workflow:
            missing.append(Obligation.TECHNICAL_METHOD.value)

    if Obligation.METRIC.value in obs:
        if _has_any(blob, _METRIC_WEAK) and not _has_any(blob, _METRIC_STRONG):
            missing.append(Obligation.METRIC.value)
        elif not _has_any(blob, _METRIC_STRONG) and "metric" not in blob:
            missing.append(Obligation.METRIC.value)

    if Obligation.STANDARD_OR_PROTOCOL.value in obs:
        if _has_any(blob, _STANDARD_WEAK) and not re.search(
            r"\b(bs|iec|ansi|nice|mhra|haccp|gdpr|iso|osha|sop)\b", blob
        ):
            missing.append(Obligation.STANDARD_OR_PROTOCOL.value)
        elif not re.search(r"\b(bs|iec|ansi|nice|mhra|haccp|gdpr|iso|osha|sop|standard|regulation|protocol)\b", blob):
            missing.append(Obligation.STANDARD_OR_PROTOCOL.value)

    if Obligation.FAILURE_MODE.value in obs:
        if _has_any(blob, _FAILURE_WEAK) and not _has_any(blob, _FAILURE_STRONG):
            missing.append(Obligation.FAILURE_MODE.value)
        elif not _has_any(blob, _FAILURE_STRONG):
            missing.append(Obligation.FAILURE_MODE.value)

    return missing


def is_pure_motivation_technical_dominance(answer: str, profile: QuestionObligationProfile) -> bool:
    """Pure motivation answer dominated by technical procedure with fit materially absent."""
    if not is_pure_motivation_profile(profile):
        return False
    blob = _blob(answer)
    has_motivation = _has_any(blob, _MOTIVATION_ANSWER_MARKERS)
    procedure_hits = sum(1 for m in _TECH_PROCEDURE_DOMINANCE if m in blob)
    if has_motivation and procedure_hits < 3:
        return False
    if not has_motivation and procedure_hits >= 2:
        return True
    if has_motivation and procedure_hits >= 4 and len(blob.split()) > 80:
        # Procedure volume overwhelms brief motivation clause.
        motiv_words = sum(1 for m in _MOTIVATION_ANSWER_MARKERS if m in blob)
        return procedure_hits > motiv_words + 2
    return False


def is_technical_only_for_hybrid(answer: str, profile: QuestionObligationProfile) -> bool:
    obs = set(profile.obligations)
    if Obligation.MOTIVATION_FIT.value not in obs and Obligation.COMPANY_FIT.value not in obs:
        return False
    blob = _blob(answer)
    return not _has_any(blob, _MOTIVATION_ANSWER_MARKERS + _COMPANY_ANSWER_MARKERS) and _has_any(
        blob, _TECH_PROCEDURE_DOMINANCE
    )


def is_motivation_only_for_hybrid(answer: str, profile: QuestionObligationProfile) -> bool:
    obs = set(profile.obligations) & MAJOR_OBLIGATIONS
    if len(obs) < 2:
        return False
    if Obligation.TECHNICAL_METHOD.value not in obs and Obligation.CONTRIBUTION.value not in obs:
        return False
    blob = _blob(answer)
    has_motivation = _has_any(blob, _MOTIVATION_ANSWER_MARKERS)
    missing = _missing_obligations(answer, profile)
    needs_more = [o for o in missing if o in obs and o != Obligation.MOTIVATION_FIT.value]
    return has_motivation and bool(needs_more)


def evaluate_answer_obligation_coverage(
    question: dict[str, Any],
    job: dict[str, Any] | None = None,
) -> dict[str, Any]:
    profile = get_question_obligation_profile(question, job)
    answer = question.get("model_answer") or ""
    missing = _missing_obligations(answer, profile)
    failures: list[str] = []
    if missing:
        failures.extend(f"missing_{m}" for m in missing)
    if is_pure_motivation_technical_dominance(answer, profile):
        failures.append("pure_motivation_technical_dominance")
    if is_technical_only_for_hybrid(answer, profile):
        failures.append("hybrid_technical_only_answer")
    if is_motivation_only_for_hybrid(answer, profile):
        failures.append("hybrid_motivation_only_answer")
    return {
        "profile": profile,
        "missing_obligations": missing,
        "failures": failures,
        "passed": not failures,
    }


def _study_blob(study: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in (
        "core_idea",
        "step_by_step_method",
        "worked_example",
        "practical_example",
        "interview_application",
        "behavioral_response_structure",
        "beginner_explanation",
        "intermediate_explanation",
        "advanced_explanation",
        "compact_explanation",
    ):
        val = study.get(key)
        if isinstance(val, list):
            parts.extend(str(v) for v in val)
        elif val:
            parts.append(str(val))
    return _blob(" ".join(parts))


def evaluate_study_obligation_coverage(
    question: dict[str, Any],
    job: dict[str, Any] | None = None,
) -> dict[str, Any]:
    profile = get_question_obligation_profile(question, job)
    study = question.get("study_material") or {}
    blob = _study_blob(study)
    missing: list[str] = []

    if Obligation.MOTIVATION_FIT.value in profile.obligations and not _has_any(blob, _MOTIVATION_ANSWER_MARKERS):
        missing.append(Obligation.MOTIVATION_FIT.value)
    if Obligation.TECHNICAL_METHOD.value in profile.obligations:
        has_method = _has_any(blob, _TECH_PROCEDURE_DOMINANCE) or (
            len(study.get("step_by_step_method") or []) >= 2
        )
        if not has_method:
            missing.append(Obligation.TECHNICAL_METHOD.value)
    if Obligation.CONTRIBUTION.value in profile.obligations and not _has_any(blob, _CONTRIBUTION_ANSWER_MARKERS):
        missing.append(Obligation.CONTRIBUTION.value)
    if Obligation.STRENGTHS.value in profile.obligations and not _has_any(blob, _STRENGTHS_ANSWER_MARKERS):
        missing.append(Obligation.STRENGTHS.value)
    if Obligation.SCENARIO_REASONING.value in profile.obligations and not _has_any(blob, _SCENARIO_ANSWER_MARKERS):
        missing.append(Obligation.SCENARIO_REASONING.value)
    if Obligation.STANDARD_OR_PROTOCOL.value in profile.obligations:
        if _has_any(blob, _STANDARD_WEAK) and not re.search(
            r"\b(bs|iec|ansi|nice|mhra|haccp|gdpr|iso|osha|sop)\b", blob
        ):
            missing.append(Obligation.STANDARD_OR_PROTOCOL.value)
        elif not re.search(
            r"\b(bs|iec|ansi|nice|mhra|haccp|gdpr|iso|osha|sop|standard|regulation|protocol)\b", blob
        ):
            missing.append(Obligation.STANDARD_OR_PROTOCOL.value)

    failures: list[str] = []
    if missing:
        failures.extend(f"missing_study_{m}" for m in missing)

    if is_pure_motivation_profile(profile):
        procedure_hits = sum(1 for m in _TECH_PROCEDURE_DOMINANCE if m in blob)
        has_motivation = _has_any(blob, _MOTIVATION_ANSWER_MARKERS)
        if procedure_hits >= 3 and not has_motivation:
            failures.append("pure_motivation_technical_procedure_study")

    return {
        "profile": profile,
        "missing_obligations": missing,
        "failures": failures,
        "passed": not failures,
    }


def is_answer_obligation_coverage_failure(question: dict[str, Any], job: dict[str, Any] | None = None) -> bool:
    profile = get_question_obligation_profile(question, job)
    if not question_in_obligation_audit_scope(question, profile):
        return False
    return not evaluate_answer_obligation_coverage(question, job)["passed"]


def is_study_obligation_coverage_failure(question: dict[str, Any], job: dict[str, Any] | None = None) -> bool:
    profile = get_question_obligation_profile(question, job)
    if not question_in_obligation_audit_scope(question, profile):
        return False
    return not evaluate_study_obligation_coverage(question, job)["passed"]


def is_synthetic_overload_failure(question: dict[str, Any], job: dict[str, Any] | None = None) -> bool:
    profile = get_question_obligation_profile(question, job)
    return profile.origin == "synthetic" and profile.synthetic_overload


def audit_answer_obligation_coverage(questions: list[dict[str, Any]], job: dict[str, Any] | None = None) -> dict[str, int]:
    return {
        "answer_obligation_coverage_failure_count": sum(
            1 for q in questions if is_answer_obligation_coverage_failure(q, job)
        )
    }


def audit_study_obligation_coverage(questions: list[dict[str, Any]], job: dict[str, Any] | None = None) -> dict[str, int]:
    return {
        "study_obligation_coverage_failure_count": sum(
            1 for q in questions if is_study_obligation_coverage_failure(q, job)
        )
    }


def audit_synthetic_overload(questions: list[dict[str, Any]], job: dict[str, Any] | None = None) -> dict[str, int]:
    return {
        "synthetic_overload_failure_count": sum(
            1 for q in questions if is_synthetic_overload_failure(q, job)
        )
    }


def audit_pure_motivation_technical_dominance(
    questions: list[dict[str, Any]], job: dict[str, Any] | None = None
) -> dict[str, int]:
    count = 0
    for q in questions:
        profile = get_question_obligation_profile(q, job)
        if not question_in_obligation_audit_scope(q, profile):
            continue
        answer = q.get("model_answer") or ""
        if is_pure_motivation_technical_dominance(answer, profile):
            count += 1
    return {"pure_motivation_technical_dominance_failure_count": count}


def audit_question_obligations(questions: list[dict[str, Any]], job: dict[str, Any] | None = None) -> dict[str, int]:
    metrics: dict[str, int] = {}
    for audit_fn in (
        audit_synthetic_overload,
        audit_answer_obligation_coverage,
        audit_study_obligation_coverage,
        audit_pure_motivation_technical_dominance,
    ):
        metrics.update(audit_fn(questions, job))
    return metrics
