from __future__ import annotations

import re
from typing import Any

from app.agents.job_search.knowledge.answer_builders import GENERIC_CLOSING_PHRASE

FORMULAIC_NATURALNESS_PATTERNS = [
    r"applies domain methods, standards, and verification controls",
    r"deliver safe and auditable outcomes",
    r"My practical workflow is:",
    r"For compliance, I check",
    r"I also apply safety checks such as",
    r"Key terms are",
]

MIN_EXPERT_NATURALNESS_SCORE = 70


def formulaic_spoken_label_count(text: str) -> int:
    if not text:
        return 0
    return sum(1 for p in FORMULAIC_NATURALNESS_PATTERNS if re.search(p, text, re.I))


def contains_formulaic_spoken_labels(text: str) -> bool:
    return formulaic_spoken_label_count(text) > 0


def _has_role_opening(answer: str, role: str, skill: str) -> bool:
    lower = (answer or "").lower()
    return role.lower() in lower or skill.lower() in lower


def _workflow_uses_domain_language(answer: str, domain_terms: list[str]) -> bool:
    hits = sum(1 for t in domain_terms[:6] if t and str(t).lower() in answer.lower())
    return hits >= 2


def expert_naturalness_score(
    answer: str,
    contract: dict[str, Any] | None = None,
    slots: dict[str, Any] | None = None,
) -> float:
    if not answer:
        return 0.0
    score = 0.0
    role = str((contract or {}).get("role") or "")
    skill = str((contract or {}).get("mapped_skill") or "")
    domain_terms = list((contract or {}).get("required_domain_terms") or [])
    if slots:
        domain_terms += list(slots.get("tools_or_documents") or [])

    if _has_role_opening(answer, role, skill):
        score += 20
    if _workflow_uses_domain_language(answer, domain_terms):
        score += 20
    if "For compliance, I would" in answer or "I would evidence the work through" in answer:
        score += 15
    if any(tok in answer.lower() for tok in ("for example", "during", "when", "on a")):
        score += 15
    mistakes = (slots or {}).get("common_mistakes") or []
    if mistakes and str(mistakes[0]).lower()[:20] in answer.lower():
        score += 10
    if answer.strip().lower().startswith("in an interview"):
        score += 10
    if not contains_formulaic_spoken_labels(answer):
        score += 10
    if GENERIC_CLOSING_PHRASE.lower() in answer.lower():
        score -= 15

    return round(min(max(score, 0.0), 100.0), 1)


def expert_naturalness_failures(
    answer: str,
    contract: dict[str, Any] | None = None,
    slots: dict[str, Any] | None = None,
) -> list[str]:
    failures: list[str] = []
    if contains_formulaic_spoken_labels(answer):
        failures.append("formulaic_spoken_label")
    if expert_naturalness_score(answer, contract, slots) < MIN_EXPERT_NATURALNESS_SCORE:
        failures.append("low_expert_naturalness")
    return failures
