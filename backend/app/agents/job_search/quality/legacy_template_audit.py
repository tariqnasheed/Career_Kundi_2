from __future__ import annotations

import re

LEGACY_TEMPLATE_PATTERNS = [
    r"Good .* work in .* means clear steps",
    r"clear steps, clear checks, and clear notes",
    r"A practical way to explain .* is this: set the goal",
    r"set the goal, run the task, verify the output",
    r"work log and sign-off note",
    r"verify output against acceptance criteria",
    r"review documentation before sign-off",
]


def legacy_template_count(text: str) -> int:
    if not text:
        return 0
    return sum(1 for p in LEGACY_TEMPLATE_PATTERNS if re.search(p, text, re.I))


def contains_legacy_template(text: str) -> bool:
    return legacy_template_count(text) > 0
