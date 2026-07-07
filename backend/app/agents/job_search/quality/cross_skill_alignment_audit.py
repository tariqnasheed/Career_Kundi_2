"""Cross-skill answer alignment audit (Defect Class D).

Independent, artifact-level detection of answers whose dominant closing claims
mastery of a skill that is NOT the question's primary skill — e.g. a Python /
Excel / Dashboarding question whose answer closes by asserting "reliable SQL
analysis".

This is a structural skill-identity check, not a phrase blacklist: it resolves
the canonical skill named in the answer's *closing claim* and compares it to the
question's primary skill. A foreign skill is only contamination when the
question does not itself invite that skill (explicit cross-skill integration is
allowed). Skills the audit does not recognise are ignored, so it never invents a
mismatch.
"""

from __future__ import annotations

import re
from typing import Any

# Bounded alias map for the closely-adjacent skills that actually get confused in
# the data family. Each alias resolves to a canonical skill identity. This is a
# small ontology, not a ban list — the audit compares identities, it does not
# forbid sentences.
_SKILL_ALIASES: dict[str, str] = {
    "sql": "sql",
    "structured query": "sql",
    "python": "python",
    "pandas": "python",
    "excel": "excel",
    "spreadsheet": "excel",
    "dashboard": "dashboarding",
    "dashboarding": "dashboarding",
    "tableau": "dashboarding",
    "power bi": "dashboarding",
    "looker": "dashboarding",
}


def _canonical_skill(text: str) -> str | None:
    low = (text or "").lower()
    for alias, canon in _SKILL_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", low):
            return canon
    return None


def _skills_named(text: str) -> set[str]:
    low = (text or "").lower()
    found: set[str] = set()
    for alias, canon in _SKILL_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", low):
            found.add(canon)
    return found


def _closing_claim(answer: str) -> str:
    """Return the answer's closing mastery claim (where dominance is asserted)."""
    a = (answer or "").strip()
    if not a:
        return ""
    m = re.search(r"in an interview[^.]*\.", a, re.IGNORECASE)
    if m:
        return m.group(0)
    sentences = re.split(r"(?<=[.!?])\s+", a)
    # Last non-empty sentence, plus a small tail for safety.
    return sentences[-1] if sentences else a


def is_cross_skill_answer_contamination(
    question: dict[str, Any], job: dict[str, Any] | None = None
) -> bool:
    primary = _canonical_skill(str(question.get("skill_tag") or ""))
    if primary is None:
        return False  # unknown primary skill — cannot assert a mismatch
    closing = _closing_claim(str(question.get("model_answer") or ""))
    closing_skills = _skills_named(closing)
    foreign = {s for s in closing_skills if s != primary}
    if not foreign:
        return False
    # Explicit cross-skill integration is legitimate: if the QUESTION itself
    # invites the foreign skill, the answer may discuss it.
    question_skills = _skills_named(str(question.get("question") or ""))
    unexplained = foreign - question_skills
    return bool(unexplained)


def audit_cross_skill_answer_alignment(
    questions: list[dict[str, Any]], job: dict[str, Any] | None = None
) -> dict[str, Any]:
    offenders: list[dict[str, Any]] = []
    for q in questions or []:
        if is_cross_skill_answer_contamination(q, job):
            offenders.append(
                {
                    "skill_tag": q.get("skill_tag"),
                    "question": (q.get("question") or "")[:120],
                }
            )
    return {
        "cross_skill_answer_contamination_failure_count": len(offenders),
        "cross_skill_answer_contamination_offenders": offenders,
    }
