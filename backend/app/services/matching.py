"""
services/matching.py
=======================
Profile Match Rating — the 0–100 "how well does this job fit me?" score shown
as a colored badge on the Job Search and Dashboard pages.

Before this module the `SavedJob.match_score` column existed and was rendered in
the UI, but nothing ever computed a value for it, so it was always `null`
(README §36 item 5). This provides a deterministic, explainable score (no LLM
call, no cost) based on how many of the job's required skills the user's profile
actually covers, weighted by how important each skill is to the role.
"""

from __future__ import annotations

from collections.abc import Iterable

# How much each importance level counts toward the score. A job's "critical"
# skills matter far more to fit than its "nice-to-have" ones.
_IMPORTANCE_WEIGHTS: dict[str, float] = {
    "critical": 3.0,
    "high": 2.0,
    "medium": 1.0,
    "nice-to-have": 0.5,
}
_DEFAULT_WEIGHT = 1.0


def _normalize(name: str) -> str:
    """Lower-case and trim a skill name so 'Python ' and 'python' compare equal."""
    return name.strip().lower()


def compute_match_score(
    user_skills: Iterable[str],
    job_skills: list[dict] | list[str],
) -> float | None:
    """
    Return a 0–100 fit score, or `None` when it can't be computed.

    Args:
        user_skills: the skill names on the user's profile (any casing).
        job_skills:  the job's extracted skills — either dicts shaped like
                     ``{"skill": "Python", "importance": "high"}`` or plain
                     strings. Unknown/missing importance defaults to "medium".

    Scoring: each job skill contributes its importance weight to the maximum
    possible score; a skill the user has contributes that same weight to the
    achieved score. The result is ``achieved / possible * 100`` rounded to one
    decimal. Returns ``None`` if the job lists no skills (so the UI can show
    "not rated" rather than a misleading 0).
    """
    if not job_skills:
        return None

    user_norm = {_normalize(s) for s in user_skills if s and s.strip()}

    possible = 0.0
    achieved = 0.0
    for entry in job_skills:
        if isinstance(entry, dict):
            name = entry.get("skill") or entry.get("name") or ""
            importance = entry.get("importance") or "medium"
        else:
            name = str(entry)
            importance = "medium"
        if not name.strip():
            continue
        weight = _IMPORTANCE_WEIGHTS.get(str(importance).lower(), _DEFAULT_WEIGHT)
        possible += weight
        if _normalize(name) in user_norm:
            achieved += weight

    if possible == 0:
        return None
    return round((achieved / possible) * 100, 1)
