"""Block silly, filler, and context-free interview questions (Iteration 004E-A)."""

from __future__ import annotations

import re
from typing import Any

_SILLY_PATTERNS: tuple[str, ...] = (
    r"\bdo you like this job\b",
    r"\bare you good at teamwork\b",
    r"\bcan you use a computer\b",
    r"\bwhat is your favou?rite tool\b",
    r"\bwhat is your favorite tool\b",
    r"\bare you passionate about\b",
    r"\bwhy should we hire you\b",
    r"\btell me about yourself\b",
    r"\bwhere do you see yourself in\b",
)

_VAGUE_ONLY_PATTERNS: tuple[str, ...] = (
    r"^what makes a good employee\??$",
    r"^how do you handle stress\??$",
    r"^are you a team player\??$",
    r"^do you work well under pressure\??$",
)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def is_silly_question(text: str) -> bool:
    lowered = _norm(text)
    return any(re.search(p, lowered) for p in _SILLY_PATTERNS)


def lacks_job_context(text: str, job: dict[str, Any], profile: dict[str, Any] | None = None) -> bool:
    """True when a question is too vague to connect to role/company/profile context."""
    lowered = _norm(text)
    if any(re.search(p, lowered) for p in _VAGUE_ONLY_PATTERNS):
        return True
    prof = profile or job.get("job_intelligence_profile") or {}
    completeness = int(prof.get("completeness_score") or 0)
    if completeness < 40:
        return False
    anchors: list[str] = []
    role = job.get("title") or ""
    if role:
        anchors.append(role.lower())
    if job.get("company_name"):
        anchors.append(str(job["company_name"]).lower())
    for key in ("responsibilities", "required_skills", "tools_software", "compliance_safety_ethics"):
        for item in prof.get(key) or []:
            token = _norm(str(item))
            if len(token) > 4:
                anchors.append(token[:40])
    if not anchors:
        return False
    if any(a and a in lowered for a in anchors if len(a) > 3):
        return False
    generic_markers = ("this role", "the role", "this position", "the company", "stakeholder", "responsibilit")
    if any(m in lowered for m in generic_markers):
        return False
    if len(lowered.split()) < 10:
        return True
    return False


def is_silly_or_vague_question(
    text: str,
    job: dict[str, Any],
    profile: dict[str, Any] | None = None,
) -> bool:
    return is_silly_question(text) or lacks_job_context(text, job, profile)
