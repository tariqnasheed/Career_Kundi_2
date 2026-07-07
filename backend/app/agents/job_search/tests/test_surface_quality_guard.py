"""Surface quality guard tests (Iteration 004E-E2.2)."""

from __future__ import annotations

from app.agents.job_search.quality.surface_quality_guard import (
    audit_surface_quality,
    fix_surface_quality_defects,
)


def test_duplicate_adjacent_tokens_detected() -> None:
    audit = audit_surface_quality("Explain the the work work sequence.")
    assert audit["duplicate_token_defects"] >= 1


def test_role_tautology_detected() -> None:
    audit = audit_surface_quality("new Mystery Role role expectations", role="Mystery Role")
    assert audit["role_tautology_defects"] >= 1


def test_incomplete_using_clause_detected() -> None:
    audit = audit_surface_quality("During a live assignment, I applied System Design using,")
    assert audit["incomplete_clause_defects"] >= 1


def test_malformed_template_detected() -> None:
    audit = audit_surface_quality("Complete Graphic Designer reliably in Graphic Designer work")
    assert audit["malformed_template_defects"] >= 1 or audit["role_tautology_defects"] >= 1


def test_fix_surface_quality_cleans_common_defects() -> None:
    fixed = fix_surface_quality_defects(
        "Explain the the work work for new Mystery Role role using,",
        role="Mystery Role",
    )
    audit = audit_surface_quality(fixed, role="Mystery Role")
    assert "the the" not in fixed
    assert audit["total_surface_quality_defects"] == 0


def test_valid_sentence_does_not_false_positive() -> None:
    text = "A strong answer could explain how you validate brand assets against the brief."
    audit = audit_surface_quality(text, role="Graphic Designer")
    assert audit["total_surface_quality_defects"] == 0


def test_malformed_coaching_conjugations_detected() -> None:
    for bad in ("You could would start the task.", "You could fixed the bug.", "You could can build it."):
        audit = audit_surface_quality(bad)
        assert audit["malformed_coaching_defects"] >= 1, bad


def test_pseudo_definition_detected() -> None:
    audit = audit_surface_quality("Domain term for Excel work that must be applied correctly.")
    assert audit["malformed_definition_defects"] >= 1


def test_fix_repairs_malformed_coaching() -> None:
    fixed = fix_surface_quality_defects(
        "You could would start. You could fixed it. You could can build the report."
    )
    low = fixed.lower()
    for bad in ("you could would", "you could fixed", "you could can"):
        assert bad not in low
    assert audit_surface_quality(fixed)["malformed_coaching_defects"] == 0


def test_midsentence_capitalisation_artifact_detected_and_fixed() -> None:
    audit = audit_surface_quality("publishing results For compliance reasons")
    assert audit["malformed_coaching_defects"] >= 1
    fixed = fix_surface_quality_defects("publishing results For compliance reasons")
    assert "results for compliance" in fixed.lower()


# --- §8/§18 generalized surface-defect classes ---


def test_article_agreement_defect_detected_and_fixed() -> None:
    """'a Electrical Engineer' -> 'an Electrical Engineer'."""
    text = "This is a Electrical Engineer role for a experienced person."
    audit = audit_surface_quality(text, role="Electrical Engineer")
    assert audit["article_agreement_defects"] >= 1
    fixed = fix_surface_quality_defects(text, role="Electrical Engineer")
    assert "an electrical engineer" in fixed.lower()
    assert "a electrical engineer" not in fixed.lower()


def test_duplicate_example_lead_in_detected_and_fixed() -> None:
    """'For example, illustrative example:' is a duplicated example introduction."""
    text = "For example, illustrative example: consider a dashboard."
    audit = audit_surface_quality(text)
    assert audit["duplicate_lead_in_defects"] >= 1
    fixed = fix_surface_quality_defects(text)
    assert "illustrative example" not in fixed.lower()


def test_repeated_phrase_construction_detected_and_fixed() -> None:
    """'performance for performance' bounded repetition."""
    text = "review dashboard refresh performance for performance today."
    audit = audit_surface_quality(text)
    assert audit["repeated_phrase_defects"] >= 1
    fixed = fix_surface_quality_defects(text)
    assert "performance for performance" not in fixed.lower()


def test_role_tautology_definition_detected_and_fixed() -> None:
    """'For a Data Analyst, Data Analyst means ...' role tautology in a definition."""
    text = "For a Data Analyst, Data Analyst means turning data into insight."
    audit = audit_surface_quality(text, role="Data Analyst")
    assert audit["role_tautology_defects"] >= 1
    fixed = fix_surface_quality_defects(text, role="Data Analyst")
    assert "data analyst, data analyst" not in fixed.lower()


def test_legitimate_repeated_technical_term_not_flagged() -> None:
    """Negative control: legitimate repetition of a technical term is not a defect."""
    text = "End-to-end testing tests the end-to-end flow before release."
    audit = audit_surface_quality(text)
    assert audit["repeated_phrase_defects"] == 0


def test_case_differing_role_tautology_detected_and_fixed() -> None:
    """§20: 'For a DevOps Engineer, Devops Engineer means …' — skill label equals the
    role but is title-cased differently, which the case-sensitive backreference missed."""
    for text, role in (
        ("For a DevOps Engineer, Devops Engineer means building and operating cloud services.", "DevOps Engineer"),
        ("For an HR Assistant, Hr Assistant means applying employment policy fairly.", "HR Assistant"),
    ):
        audit = audit_surface_quality(text, role=role)
        assert audit["role_tautology_defects"] >= 1, text
        fixed = fix_surface_quality_defects(text, role=role)
        assert ", this means" in fixed
        assert audit_surface_quality(fixed, role=role)["role_tautology_defects"] == 0


def test_role_then_distinct_skill_definition_not_flagged() -> None:
    """Negative control: a legitimate 'For a {role}, {skill} means …' where skill is a
    genuine distinct skill must not be flagged as a tautology."""
    text = "For a Data Analyst, SQL means turning raw data into reliable insight."
    audit = audit_surface_quality(text, role="Data Analyst")
    assert audit["role_tautology_defects"] == 0
