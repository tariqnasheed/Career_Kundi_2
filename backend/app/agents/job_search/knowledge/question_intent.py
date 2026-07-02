from __future__ import annotations

import re

INTENT_TERMINOLOGY = "terminology_definition"
INTENT_CALCULATION = "calculation_or_diagnostic"
INTENT_SCENARIO = "scenario_case"
INTENT_PEER = "peer_teaching"
INTENT_PRINCIPLES = "principles_workflow"
INTENT_PRODUCTION = "production_issue_metrics"
INTENT_GENERAL = "general_explain"

_QTYPE_TO_INTENT = {
    "terminology": INTENT_TERMINOLOGY,
    "calculation": INTENT_CALCULATION,
    "scenario": INTENT_SCENARIO,
    "complex_problem": INTENT_SCENARIO,
    "explain_to_peer": INTENT_PEER,
    "principles": INTENT_PRINCIPLES,
    "procedure": INTENT_PRINCIPLES,
    "behavioral": INTENT_GENERAL,
    "motivation": INTENT_GENERAL,
    "company_research": INTENT_GENERAL,
}

_NON_TECHNICAL_CATEGORIES = {
    "behavioral",
    "role_specific",
    "company_specific",
    "system_design",
}

_BEHAVIORAL_MARKERS = (
    "tell me about",
    "describe a time",
    "describe a ",
    "describe one ",
    "give an example",
    "give a case",
    "share a ",
    "share an ",
    "this role involves",
    "what excites you",
    "what do you know about",
    "why do you want",
)


def detect_question_intent(
    question: str,
    question_type: str | None = None,
    *,
    category: str | None = None,
) -> str:
    text = (question or "").lower()
    qtype = (question_type or "").lower()
    cat = (category or "").lower()

    if cat in _NON_TECHNICAL_CATEGORIES or qtype in {"behavioral", "motivation", "company_research"}:
        return INTENT_GENERAL
    if any(marker in text for marker in _BEHAVIORAL_MARKERS):
        return INTENT_GENERAL

    if qtype in _QTYPE_TO_INTENT:
        mapped = _QTYPE_TO_INTENT[qtype]
        if mapped == INTENT_SCENARIO and any(
            k in text for k in ("impact metric", "production issue", "complex production", "including impact")
        ):
            return INTENT_PRODUCTION
        if mapped == INTENT_CALCULATION and any(
            k in text for k in ("why does", "perform poorly", "diagnose", "lookup", "index seek")
        ):
            return INTENT_CALCULATION
        return mapped

    if any(k in text for k in ("terminology", "define each", "critical terms", "essential technical terms", "vocabulary separates")):
        return INTENT_TERMINOLOGY
    if any(
        k in text
        for k in (
            "why does",
            "calculate",
            "10 million rows",
            "index on",
            "index seek",
            "lookup",
            "perform poorly",
            "quantitative",
            "numbers-driven",
            "calculation /",
        )
    ):
        return INTENT_CALCULATION
    if any(k in text for k in ("impact metric", "production issue", "complex production", "including impact")):
        return INTENT_PRODUCTION
    if any(k in text for k in ("high-risk", "high-stakes", "describe a case", "clinical case", "scenario")):
        return INTENT_SCENARIO
    if any(k in text for k in ("junior engineer", "explain to a junior", "trade-off", "trade-offs", "newly qualified", "apprentice")):
        return INTENT_PEER
    if any(
        k in text
        for k in ("core operating principles", "standard workflow", "non-negotiable rules", "execution sequence")
    ):
        return INTENT_PRINCIPLES
    if any(k in text for k in ("explain", "walk me through", "how would you teach", "break down")):
        return INTENT_GENERAL
    return INTENT_GENERAL
