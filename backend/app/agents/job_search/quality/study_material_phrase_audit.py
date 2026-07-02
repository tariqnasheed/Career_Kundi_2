from __future__ import annotations

import re

from app.agents.job_search.quality.generic_phrase_audit import GENERIC_PATTERNS, generic_phrase_count

STUDY_BANNED_PATTERNS = list(GENERIC_PATTERNS) + [
    r"\bin this context\b",
    r"\bthe critical discipline is evidence\b",
    r"\bkey terms are\b",
    r"\bthis skill is important because\b",
    r"\byou should understand the basics\b",
    r"\bhelps in many industries\b",
    r"\bgeneric wording\b",
    r"\bmissing final verification\b",
    r"\bbenchmark check\b",
    r"\bdocumentation review\b",
    r"\bacceptance criteria\b",
    r"\bstructured verification\b",
    r"\bdo safe and correct work\b",
]

PLACEHOLDER_PATTERNS = [
    r"\bTBD\b",
    r"\bTODO\b",
    r"\bLorem ipsum\b",
    r"\[insert\b",
    r"\{\{",
    r"\?\?\?",
    r"<placeholder>",
]


def study_banned_phrase_count(text: str) -> int:
    if not text:
        return 0
    return sum(1 for p in STUDY_BANNED_PATTERNS if re.search(p, text, re.I))


def study_placeholder_count(text: str) -> int:
    if not text:
        return 0
    return sum(1 for p in PLACEHOLDER_PATTERNS if re.search(p, text, re.I))


def contains_study_banned_phrase(text: str) -> bool:
    return study_banned_phrase_count(text) > 0
