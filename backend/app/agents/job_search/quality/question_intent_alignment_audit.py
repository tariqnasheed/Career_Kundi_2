from __future__ import annotations

import re
from typing import Any

from app.agents.job_search.knowledge.answer_builders import GENERIC_CLOSING_PHRASE
from app.agents.job_search.knowledge.question_intent import detect_question_intent

TERM_DEFINITION_PATTERN = re.compile(r"\*\*[^*]+\*\*\s+means\b", re.I)
WORKFLOW_ONLY_MARKERS = (
    "i would start by",
    "for compliance, i would rely on",
    "i would evidence the work through",
)


def _count_term_definitions(answer: str) -> int:
    return len(TERM_DEFINITION_PATTERN.findall(answer or ""))


def _has_tradeoff_language(answer: str) -> bool:
    lower = (answer or "").lower()
    return any(
        tok in lower
        for tok in (
            "trade-off",
            "trade off",
            "trade-offs",
            "versus",
            " vs ",
            "balance",
            "speed against",
            "cost against",
            " trade ",
            " against ",
            "but can slow",
            "but cost more",
        )
    )


def _has_measurable_signal(answer: str) -> bool:
    lower = (answer or "").lower()
    return any(
        tok in lower
        for tok in (
            "mttr",
            "failure rate",
            "alarm coverage",
            "rollback time",
            "logical reads",
            "runtime",
            "query runtime",
            "kpi",
            "metric",
            "measurable",
            "seconds to",
            "reduced",
            "cut ",
            "clinical response",
            "patient stabil",
            "deterioration",
            "adverse event",
            "dosage",
            "observations",
            "10 minutes",
            "58%",
            "76%",
            "7%",
            "0.2%",
            "compliance",
            "verified",
            "test results",
            "measured values",
            "within sla",
            "within tolerance",
            "insulation resistance",
            "calibration",
        )
    )


def _is_workflow_only(answer: str, intent: str) -> bool:
    if intent in {"terminology_definition", "calculation_or_diagnostic", "peer_teaching"}:
        lower = (answer or "").lower()
        hits = sum(1 for marker in WORKFLOW_ONLY_MARKERS if marker in lower)
        if intent == "terminology_definition" and _count_term_definitions(answer) < 4:
            return True
        if intent == "calculation_or_diagnostic" and not any(
            tok in lower
            for tok in ("select only", "covering index", "execution plan", "logical reads", "bookmark", "i/o")
        ):
            return hits >= 2 and "why" in (answer or "").lower()
        if intent == "peer_teaching" and (not _has_tradeoff_language(answer) or not _has_measurable_signal(answer)):
            return True
    return False


def audit_question_intent_alignment(
    answer: str,
    question: dict[str, Any],
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    text = answer or ""
    question_text = str(question.get("question") or "")
    intent = detect_question_intent(
        question_text,
        question.get("question_type"),
        category=question.get("category"),
    )
    lower = text.lower()

    if intent == "terminology_definition":
        term_count = _count_term_definitions(text)
        if term_count < 4:
            errors.append(
                f"terminology question requires >= 4 term definitions (expected >= 4, actual {term_count})"
            )
        if "means" not in lower:
            errors.append("terminology answer missing definition language ('means')")

    elif intent == "calculation_or_diagnostic":
        diagnostic_hits = sum(
            1
            for tok in (
                "select only",
                "needed columns",
                "covering index",
                "execution plan",
                "logical reads",
                "bookmark",
                "i/o",
                "heap",
                "clustered",
            )
            if tok in lower
        )
        if "why does" in question_text.lower() or "perform poorly" in question_text.lower():
            if diagnostic_hits < 3:
                errors.append(
                    f"diagnostic answer does not directly explain the stated issue "
                    f"(expected >= 3 diagnostic markers, actual {diagnostic_hits})"
                )

    elif intent == "peer_teaching":
        if not _has_tradeoff_language(text):
            errors.append("peer-teaching answer missing trade-off language")
        if not _has_measurable_signal(text):
            errors.append("peer-teaching answer missing measurable quality signal")

    elif intent == "scenario_case":
        if not any(tok in lower for tok in ("case", "patient", "risk", "escalat", "document")):
            errors.append("scenario answer missing case/risk/action/documentation language")

    elif intent == "production_issue_metrics":
        if not any(tok in lower for tok in ("issue", "diagnos", "fix", "metric", "runtime", "seconds", "kpi")):
            errors.append("production-issue answer missing issue/diagnosis/fix/metric language")

    elif intent == "principles_workflow":
        if not any(tok in lower for tok in ("principle", "workflow", "govern", "standard workflow")):
            errors.append("principles answer missing named principles and workflow language")

    if _is_workflow_only(text, intent):
        errors.append(f"answer falls back to generic workflow body for intent '{intent}'")

    if GENERIC_CLOSING_PHRASE.lower() in lower:
        warnings.append("answer uses repeated generic closing phrase")

    passed = not errors
    score = max(0.0, round(100.0 - (len(errors) * 20) - (len(warnings) * 5), 1))
    return {
        "passed": passed,
        "score": score,
        "intent": intent,
        "errors": errors,
        "warnings": warnings,
    }
