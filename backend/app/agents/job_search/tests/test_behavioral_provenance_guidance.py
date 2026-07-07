"""Provenance-aware behavioral study guidance tests (004E-E2.3 §13).

For unknown / not-provided provenance the study guidance must not pressure the
user to close with quantified results or treat a hypothetical scenario as a
mistake. It must invite a real example where one exists, numbers only when
genuinely known, and clearly hypothetical practice otherwise. When the user has
provided genuine experience, the stronger "use your real numbers" guidance is
kept without weakening their claims.
"""

from __future__ import annotations

from app.agents.job_search.knowledge.content_engine import (
    _soften_metric_pressure_principles,
    build_study_material,
    get_role_context,
)


def _blob(study: dict) -> str:
    parts: list[str] = []
    for value in study.values():
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            parts.extend(str(v) for v in value)
    return " ".join(parts).lower()


_THIN_JOB = {
    "title": "Senior Systems Engineer",
    "responsibilities": ["production incident response"],
    "extracted_skills": [{"skill": "Linux"}],
}
_EXPERIENCED_JOB = {
    "title": "Senior Systems Engineer",
    "responsibilities": ["production incident response"],
    "extracted_skills": [{"skill": "Linux"}],
    "profile_summary": "I ran on-call for three years handling production outages.",
    "achievements": ["Cut MTTR by improving runbooks"],
}
_BEHAVIORAL_Q = {
    "question": "Tell me about a time you handled a production incident.",
    "category": "behavioral",
    "question_type": "behavioral",
}


def test_unknown_provenance_does_not_pressure_numbers() -> None:
    study = build_study_material(_BEHAVIORAL_Q, _THIN_JOB)
    blob = _blob(study)
    # No unconditional demand to close with quantified results / use numbers.
    assert "close with quantified results" not in blob
    assert "with numbers" not in blob
    # Hypothetical practice is offered, and numbers are conditioned on genuine knowledge.
    assert "hypothetical" in blob
    assert "genuinely" in blob


def test_unknown_provenance_does_not_forbid_hypothetical() -> None:
    study = build_study_material(_BEHAVIORAL_Q, _THIN_JOB)
    mistakes = " ".join(str(m).lower() for m in (study.get("common_mistakes") or []))
    # The old guidance wrongly treated hypothetical answers as a mistake.
    assert "hypothetical answers instead of real events" not in mistakes
    # Inventing history is the real mistake to warn against.
    assert "inventing" in mistakes


def test_experienced_provenance_keeps_genuine_numbers_guidance() -> None:
    study = build_study_material(_BEHAVIORAL_Q, _EXPERIENCED_JOB)
    blob = _blob(study)
    # With genuine experience, guidance may reference the user's real numbers,
    # but must still tie numbers to authenticity ("genuine").
    assert "genuine numbers" in blob or "your genuine numbers" in blob
    assert "genuinely" in blob or "genuine" in blob


def test_soften_metric_pressure_rewrites_measurable_outcomes() -> None:
    """Unit: the generated 'concrete examples with scale ... measurable outcomes'
    expectation is rewritten to a provenance-aware form; non-metric expectations
    are preserved verbatim."""
    raw = [
        "Explain how Pharmacology supports daily responsibilities when asked.",
        "Use concrete examples with scale, constraints, stakeholders, and measurable outcomes.",
        "Reference professional standards, regulations, or best-practice frameworks.",
    ]
    softened = _soften_metric_pressure_principles(raw)
    # Non-metric principles unchanged.
    assert softened[0] == raw[0]
    assert softened[2] == raw[2]
    # The metric-pressure principle is now conditioned on genuine knowledge.
    assert "only where you genuinely have them" in softened[1].lower()
    assert "measurable outcomes." != softened[1].split()[-1]


def test_role_with_metric_expectations_softened_for_unknown_provenance() -> None:
    """End-to-end: a role whose generated role-context pressures 'measurable
    outcomes' must not emit that unconditional pressure for an unknown-provenance
    behavioral/HR module — the fixed guidance replaces it with a genuine-knowledge
    caveat. This discriminates: the raw role context still contains the pressure."""
    role_ctx = get_role_context("Clinical Pharmacist")
    raw_expectations = " ".join(role_ctx.get("what_employers_expect", [])).lower()
    # Guard: this test only discriminates if the source data still has the pressure.
    assert "measurable outcomes" in raw_expectations
    assert "only where you genuinely have them" not in raw_expectations

    thin_job = {
        "title": "Clinical Pharmacist",
        "responsibilities": ["medication review"],
        "extracted_skills": [{"skill": "Pharmacology"}],
    }
    hr_q = {
        "question": "Why do you want this Clinical Pharmacist role and how would you "
        "contribute to medicines optimisation?",
        "category": "hr",
        "question_type": "hr",
    }
    study = build_study_material(hr_q, thin_job)
    principles = [str(p).lower() for p in (study.get("key_principles") or study.get("principles") or [])]
    joined = " ".join(principles)
    # The unconditional pressure must be gone; any surviving mention is caveated.
    for p in principles:
        if "measurable outcomes" in p:
            assert "only where you genuinely have them" in p, p
    # A genuine-knowledge caveat is present somewhere in the guidance.
    assert "genuinely have them" in joined
