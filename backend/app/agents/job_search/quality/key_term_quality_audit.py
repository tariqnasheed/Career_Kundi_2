from __future__ import annotations

import re

_INVALID_PREFIXES = (
    "outcome",
    "traceability",
    "risk controls",
    "quality improves",
    "failure prevents",
)
_INVALID_SUFFIXES = ("when", "into", "with", "because", "no", "and", "or")
_INVALID_VERB_PATTERNS = (
    "improves",
    "prevents",
    "must be",
    "should be",
    "can be",
    "needs to",
)


def is_valid_key_term(term: str) -> bool:
    t = (term or "").strip()
    if not t:
        return False
    if len(t.split()) > 5:
        return False
    lower = t.lower()
    if lower.startswith(_INVALID_PREFIXES):
        return False
    if lower.endswith(_INVALID_SUFFIXES):
        return False
    if any(v in lower for v in _INVALID_VERB_PATTERNS):
        return False
    if re.search(r"[.!?]", t):
        return False
    return True


def invalid_key_terms(terms: list[str]) -> list[str]:
    return [t for t in terms if not is_valid_key_term(t)]


def invalid_key_term_count_in_answer(answer: str) -> int:
    if not answer:
        return 0
    count = 0
    bad_fragments = [
        "Outcome quality improves when assumption",
        "Traceability prevents repeated failures",
        "Risk controls must be integrated into no",
    ]
    for frag in bad_fragments:
        if frag.lower() in answer.lower():
            count += 1
    return count
