"""Terminology integrity audit (Defect Class B).

Independent, artifact-level detection of prose fragments that have been promoted
into professional terminology. This does NOT rely on a phrase blacklist: it
reuses the structural :func:`is_valid_key_term` boundary (a term must be a
short, noun-like domain concept / named tool / standard — not a clipped prose
principle or sentence fragment) and applies it to the FINAL exported question
text and its ``terminology_terms`` payload.

A term is malformed when it fails the structural boundary. The audit inspects
both the explicit ``terminology_terms`` list and the comma-separated term list
embedded in the exported question ("...define and explain these core
professional terms: A, B, C."), because a real exported artifact is judged on
what a candidate actually reads, not only on the internal object.
"""

from __future__ import annotations

import re
from typing import Any

from app.agents.job_search.quality.key_term_quality_audit import is_valid_key_term

_TERM_LIST_RE = re.compile(r"terms?\s*:\s*(.+?)\s*\.?\s*$", re.IGNORECASE | re.DOTALL)


def _is_terminology_question(q: dict[str, Any]) -> bool:
    qtype = (q.get("question_type") or "").lower()
    if qtype == "terminology":
        return True
    # Fall back to shape: a consolidated terminology question carries the list.
    return bool(q.get("terminology_terms"))


def _terms_in_question_text(question: str) -> list[str]:
    """Extract the comma-separated term list a candidate actually reads.

    The term list ends at the first sentence boundary; anything after it (e.g. a
    later "In this role-specific case, address: …" uniqueness suffix) is NOT part
    of the terminology list and must not be mistaken for a malformed term.
    """
    if not question:
        return []
    marker = "professional terms:"
    idx = question.lower().rfind(marker)
    if idx != -1:
        tail = question[idx + len(marker):]
    else:
        m = _TERM_LIST_RE.search(question)
        if not m:
            return []
        tail = m.group(1)
    # Stop at the first sentence boundary — the term list is a single sentence.
    tail = re.split(r"\.\s|\.$", tail.strip(), maxsplit=1)[0]
    tail = tail.strip().rstrip(".")
    return [seg.strip() for seg in tail.split(",") if seg.strip()]


def malformed_terms_in_question(q: dict[str, Any]) -> list[str]:
    """Return the distinct malformed terminology candidates for one question."""
    bad: list[str] = []
    seen: set[str] = set()

    def _consider(term: str) -> None:
        t = (term or "").strip()
        key = t.lower()
        if not t or key in seen:
            return
        if not is_valid_key_term(t):
            seen.add(key)
            bad.append(t)

    for entry in q.get("terminology_terms") or []:
        if isinstance(entry, dict):
            _consider(str(entry.get("term") or ""))
        else:
            _consider(str(entry))

    for term in _terms_in_question_text(q.get("question") or ""):
        _consider(term)

    return bad


def audit_terminology_integrity(questions: list[dict[str, Any]]) -> dict[str, Any]:
    """Count terminology questions carrying at least one malformed prose term.

    The failure count is per-question (an artifact-level defect), and the
    offending terms are returned for actionable reporting.
    """
    failures = 0
    offenders: list[dict[str, Any]] = []
    for q in questions or []:
        if not _is_terminology_question(q):
            continue
        bad = malformed_terms_in_question(q)
        if bad:
            failures += 1
            offenders.append({"question": (q.get("question") or "")[:120], "terms": bad})
    return {
        "terminology_integrity_failure_count": failures,
        "terminology_integrity_offenders": offenders,
    }
