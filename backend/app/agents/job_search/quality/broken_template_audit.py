from __future__ import annotations

import re

BROKEN_PATTERNS = [
    r"A real example:\s*(The key control|Core terms|$)",
    r"\.\,",
    r"\.\.",
    r"assumption,\s*Traceability",
    r"Outcome quality improves when assumption",
    r"develop architectural designs with consistent quality",
    r"prepare drinks to standard with consistent quality",
]

BROKEN_PATTERN_BUCKETS = {
    "legacy_template_leak": [
        r"Good .* work in .* means clear steps",
        r"A practical way to explain .* is this: set the goal",
    ],
    "generic_fragment": [
        r"Outcome quality improves when assumption",
        r"prepare drinks to standard with consistent quality",
        r"develop architectural designs with consistent quality",
    ],
    "punctuation_artifact": [
        r"\.\,",
        r"\.\.",
        r"assumption,\s*Traceability",
    ],
    "weak_example_marker": [
        r"A real example:\s*(The key control|Core terms|$)",
    ],
    "internal_quality_language": [
        r"acceptance criteria",
        r"benchmark check",
        r"documentation review",
    ],
}


def broken_template_count(text: str) -> int:
    if not text:
        return 0
    return sum(1 for p in BROKEN_PATTERNS if re.search(p, text, re.I))


def contains_broken_pattern(text: str) -> bool:
    return broken_template_count(text) > 0


def broken_pattern_breakdown(text: str) -> dict[str, int]:
    if not text:
        return {k: 0 for k in BROKEN_PATTERN_BUCKETS}
    out: dict[str, int] = {}
    for bucket, patterns in BROKEN_PATTERN_BUCKETS.items():
        out[bucket] = sum(1 for p in patterns if re.search(p, text, re.I))
    return out
