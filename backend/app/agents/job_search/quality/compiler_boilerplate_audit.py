from __future__ import annotations

import re

from app.agents.job_search.quality.blocked_phrase_guard import COMPILER_BOILERPLATE_EXTRA

COMPILER_BOILERPLATE_PATTERNS = [
    r"this is not a single action",
    r"preparation, controlled execution, verification, and safe handover",
    r"without validating prerequisites and constraints",
    r"I would show both technical method and safety responsibility",
    r"Key terms in this task are",
]

NEW_COMPILER_BOILERPLATE_PATTERNS = [
    r"In this .* context, .* starts with",
    r"and continues through",
    r"The critical discipline is evidence",
    r"When conditions change, I revalidate assumptions before proceeding",
    r"stays reliable under real operational constraints",
    r"gather and reconcile source documents against assertions",
    r"materiality drives prioritization of review effort",
] + list(COMPILER_BOILERPLATE_EXTRA)

UNIVERSAL_BOILERPLATE_PATTERNS = COMPILER_BOILERPLATE_PATTERNS + NEW_COMPILER_BOILERPLATE_PATTERNS


def universal_boilerplate_count(text: str) -> int:
    if not text:
        return 0
    return sum(1 for p in UNIVERSAL_BOILERPLATE_PATTERNS if re.search(p, text, re.I))


def compiler_boilerplate_count(text: str) -> int:
    return universal_boilerplate_count(text)


def contains_universal_boilerplate(text: str) -> bool:
    return universal_boilerplate_count(text) > 0
