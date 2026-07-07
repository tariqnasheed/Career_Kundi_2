"""Generic template saturation audit (Defect Class F).

Detects systemic reuse of the SAME generic sentence skeleton across unrelated
skills — the tell-tale sign that deterministic fallback prose (e.g. "Clear scope
and verification steps keep <skill> work predictable in <role> settings.") is
dominating real, skill-specific content.

This is NOT a phrase blacklist. Each sentence is reduced to a skeleton by
substituting the role and skill tokens with a placeholder and normalising
whitespace; a skeleton shared by three or more DISTINCT skills is treated as
saturation. A single occurrence — or the same compliance line reused by two
skills — is allowed within bounded limits.
"""

from __future__ import annotations

import re
from typing import Any

# A skeleton must be a meaningful sentence before repetition counts as
# saturation; trivially short structural fragments ("Overview of <skill>.") are
# ignored so ordinary scaffolding is not mistaken for template dominance.
_MIN_SKELETON_WORDS = 6
# Number of distinct skills that must share one skeleton for it to count as
# systemic saturation (2 is an allowed bounded repeat; 3+ is systemic).
_SATURATION_SKILL_THRESHOLD = 3


def _skeleton(text: str, role: str, skill: str) -> str:
    out = (text or "").lower()
    for token in (skill or "", role or ""):
        token = token.strip().lower()
        if token:
            out = out.replace(token, "@")
    out = re.sub(r"[^a-z@ ]+", " ", out)
    return re.sub(r"\s+", " ", out).strip()


def _study_sentences(study: dict[str, Any]) -> list[str]:
    """Content sentences where GENERIC filler dominates.

    Scoped to declarative principle / fact content — NOT interview-coaching
    scaffolds ("structure your spoken answer around …") or step-by-step workflow,
    which are legitimately repeated as scaffolding and are not the generic-content
    saturation Defect Class F targets.
    """
    sentences: list[str] = []
    if not isinstance(study, dict):
        return sentences
    for key in ("principles", "key_facts"):
        for item in study.get(key) or []:
            if isinstance(item, str) and item.strip():
                sentences.append(item)
    for key in ("core_idea", "overview"):
        val = study.get(key)
        if isinstance(val, str) and val.strip():
            sentences.append(val)
    return sentences


def audit_template_saturation(
    questions: list[dict[str, Any]],
    *,
    role: str = "",
    skills: list[str] | None = None,
) -> dict[str, Any]:
    """Flag sentence skeletons shared across >= 3 distinct skills."""
    skeleton_skills: dict[str, set[str]] = {}
    for q in questions or []:
        skill = str(q.get("skill_tag") or "")
        study = q.get("study_material") or {}
        for sentence in _study_sentences(study):
            skel = _skeleton(sentence, role, skill)
            if len(skel.split()) < _MIN_SKELETON_WORDS:
                continue
            skeleton_skills.setdefault(skel, set()).add(skill.lower())

    saturated = {
        skel: sorted(sk)
        for skel, sk in skeleton_skills.items()
        if len(sk) >= _SATURATION_SKILL_THRESHOLD
    }
    return {
        "generic_template_saturation_failure_count": len(saturated),
        "generic_template_saturation_skeletons": [
            {"skeleton": skel[:120], "skills": sk} for skel, sk in list(saturated.items())[:8]
        ],
    }
