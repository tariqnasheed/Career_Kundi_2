from __future__ import annotations

import re

from app.agents.job_search.quality.blocked_phrase_guard import (
    CLARIFY_OUTCOME,
    GENERIC_PHRASE_PATTERN,
    VALIDATE_ACCEPTANCE,
)

GENERIC_PATTERNS = [
    r"\bdisciplined way we deliver\b",
    r"\bconsistent quality\b",
    r"\bclear steps\b",
    r"\bclear checks\b",
    r"\bclear notes\b",
    r"\bquality steady\b",
    r"\bclean .* note\b",
    r"\bcore terms I watch closely\b",
    r"\bwhat employers expect is this\b",
    r"\bdo safe and correct work\b",
    re.escape(CLARIFY_OUTCOME),
    re.escape(VALIDATE_ACCEPTANCE),
    r"\bfix issues early\b",
    GENERIC_PHRASE_PATTERN,
    r"\bdocumented the control points\b",
    r"\bcomplaint rate decreased materially\b",
]


def generic_phrase_count(text: str) -> int:
    if not text:
        return 0
    return sum(1 for p in GENERIC_PATTERNS if re.search(p, text, re.I))


def contains_generic_pattern(text: str) -> bool:
    return generic_phrase_count(text) > 0
