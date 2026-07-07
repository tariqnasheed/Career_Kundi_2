"""Cross-domain contamination tests (Iteration 004E-E2.2)."""

from __future__ import annotations

from app.agents.job_search.knowledge.evidence_packs import get_evidence_pack_for_question
from app.agents.job_search.quality.cross_domain_guard import audit_cross_domain_contamination


def test_graphic_designer_blocks_journalism_without_source() -> None:
    text = "For a breaking story I verified independent sources and obtained sub-editor sign-off."
    audit = audit_cross_domain_contamination(
        text,
        role="Graphic Designer",
        skill="Brand Design",
        job={"title": "Graphic Designer", "responsibilities": ["Create visual assets"]},
    )
    assert audit["cross_domain_contamination_hits"] >= 1


def test_graphic_designer_blocks_marketing_without_source() -> None:
    text = "Qualified lead rate improved through CRM funnel hygiene and audience segmentation."
    audit = audit_cross_domain_contamination(
        text,
        role="Graphic Designer",
        skill="Adobe Creative Suite",
        job={"title": "Graphic Designer"},
    )
    assert audit["cross_domain_contamination_hits"] >= 1


def test_journalist_allows_journalism_content() -> None:
    text = "I verified independent sources and followed editorial policy before headline sign-off."
    audit = audit_cross_domain_contamination(
        text,
        role="Journalist",
        skill="Reporting",
        job={"title": "Journalist"},
    )
    assert audit["cross_domain_contamination_hits"] == 0


def test_marketing_specialist_allows_funnel_content() -> None:
    text = "Campaign funnel conversion improved through audience segmentation and CRM hygiene."
    audit = audit_cross_domain_contamination(
        text,
        role="Marketing Specialist",
        skill="Demand Generation",
        job={"title": "Marketing Specialist"},
    )
    assert audit["cross_domain_contamination_hits"] == 0


def test_graphic_designer_pack_is_design_not_journalism() -> None:
    pack = get_evidence_pack_for_question("creative_media", "Graphic Designer", "Brand Design")
    examples = " ".join(pack.get("role_specific_examples") or [])
    terms = " ".join(pack.get("domain_terms") or [])
    assert "breaking story" not in examples.lower()
    assert "visual hierarchy" in terms.lower()


def test_excel_flags_sql_execution_plan_content() -> None:
    audit = audit_cross_domain_contamination(
        "review query execution plans for performance and schema design",
        role="Data Analyst",
        skill="Excel",
        job={"title": "Data Analyst", "responsibilities": ["Build dashboards"]},
    )
    assert audit["cross_domain_contamination_hits"] >= 1
    assert any("execution plan" in t for t in audit["skill_foreign_term_hits"])


def test_excel_flags_db_qps_answer() -> None:
    audit = audit_cross_domain_contamination(
        "Size the connection pool for 2000 QPS to the database to avoid saturation.",
        role="Data Analyst",
        skill="Excel",
        job={"title": "Data Analyst"},
    )
    assert audit["cross_domain_contamination_hits"] >= 1


def test_data_analyst_excel_flags_foreign_profession_framing() -> None:
    audit = audit_cross_domain_contamination(
        "This mirrors how Chartered Accountant professionals reconcile ledgers.",
        role="Data Analyst",
        skill="Excel",
        job={"title": "Data Analyst", "responsibilities": ["Build dashboards"]},
    )
    assert audit["cross_domain_contamination_hits"] >= 1
    assert "chartered accountant" in audit["foreign_role_hits"]


def test_generated_excel_content_is_scrubbed_of_sql_terms() -> None:
    from app.agents.job_search.mock_data import _scrub_skill_foreign_terms, _skill_scrub_rules

    rules = _skill_scrub_rules("Excel")
    scrubbed = _scrub_skill_foreign_terms(
        "Review query execution plans and schema design; size the connection pool for QPS.",
        rules,
    ).lower()
    for term in ("query execution plan", "execution plan", "schema design", "connection pool", "qps"):
        assert term not in scrubbed


def test_sql_skill_keeps_legitimate_sql_terms() -> None:
    from app.agents.job_search.mock_data import _scrub_skill_foreign_terms, _skill_scrub_rules

    # A genuine SQL question must NOT be scrubbed.
    rules = _skill_scrub_rules("SQL")
    text = "Review the query execution plan and schema design."
    assert _scrub_skill_foreign_terms(text, rules) == text


def test_hybrid_role_can_justify_marketing_when_posting_requires_it() -> None:
    job = {
        "title": "Graphic Designer",
        "responsibilities": ["Collaborate with marketing on campaign assets"],
        "description_raw": "Support demand generation campaigns with on-brand creative assets.",
    }
    text = "I aligned campaign assets with audience segmentation guidance from marketing."
    audit = audit_cross_domain_contamination(
        text,
        role="Graphic Designer",
        skill="Brand Design",
        job=job,
    )
    assert audit["contamination_status"] in {"clean", "source_justified"}
