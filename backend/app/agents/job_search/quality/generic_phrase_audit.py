from __future__ import annotations

import re

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
    r"\bclarify required outcome, constraints, and stakeholders\b",
    r"\bvalidate output against acceptance criteria\b",
    r"\bfix issues early\b",
    r"\bstructured verification\b",
    r"\bdocumented the control points\b",
    r"\bcomplaint rate decreased materially\b",
]


def generic_phrase_count(text: str) -> int:
    if not text:
        return 0
    return sum(1 for p in GENERIC_PATTERNS if re.search(p, text, re.I))


def contains_generic_pattern(text: str) -> bool:
    return generic_phrase_count(text) > 0
