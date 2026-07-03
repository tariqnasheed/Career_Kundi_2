from __future__ import annotations

from app.agents.job_search.quality.blocked_phrase_guard import (
    DOCUMENTED_CONTROL_POINTS,
    STRUCTURED_VERIFICATION,
)

_WEAK_EXAMPLE_PATTERNS = (
    STRUCTURED_VERIFICATION,
    DOCUMENTED_CONTROL_POINTS,
    "stabilized workflow",
    "complaint rate decreased materially",
    "reduced rework",
    "improved outcomes",
)


def has_weak_example(example: str) -> bool:
    lowered = (example or "").lower()
    return any(p in lowered for p in _WEAK_EXAMPLE_PATTERNS)


def validate_example_quality(example: str, required_domain_terms: list[str]) -> list[str]:
    failures: list[str] = []
    ex = (example or "").strip()
    if len(ex.split()) < 25:
        failures.append("truncated_example")
        return failures
    lowered = ex.lower()
    hits = sum(1 for t in required_domain_terms if t and str(t).lower() in lowered)
    if hits < 2:
        failures.append("generic_surface_fragment")
    if has_weak_example(ex):
        failures.append("generic_surface_fragment")
    return failures
