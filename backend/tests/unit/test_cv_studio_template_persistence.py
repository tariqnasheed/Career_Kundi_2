"""
Unit tests for CVB-F4 studio template persistence helpers
(app/agents/cv_builder/studio_template.py) and CVRead hydration.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.agents.cv_builder.studio_template import (
    ALLOWED_STUDIO_TEMPLATE_IDS,
    DEFAULT_STUDIO_TEMPLATE_ID,
    extract_studio_template_id,
    inject_studio_template_id,
    resolve_studio_template_id,
    validate_studio_template_id,
    visible_section_config,
)
from app.schemas.cv_builder import CVGenerateRequest, CVRead, CVUpdateRequest


def test_allowed_studio_ids_match_catalog_count():
    assert len(ALLOWED_STUDIO_TEMPLATE_IDS) == 15
    assert "minimal-corporate" in ALLOWED_STUDIO_TEMPLATE_IDS
    assert "bold-sidebar" in ALLOWED_STUDIO_TEMPLATE_IDS


def test_validate_studio_template_id_accepts_known_and_rejects_unknown():
    assert validate_studio_template_id("bold-sidebar") == "bold-sidebar"
    assert validate_studio_template_id(None) is None
    assert validate_studio_template_id("") is None
    with pytest.raises(ValueError, match="Unknown studio_template_id"):
        validate_studio_template_id("not-a-real-template")


def test_inject_and_extract_roundtrip():
    base = [{"section_id": "summary", "enabled": True}]
    with_meta = inject_studio_template_id(base, "editorial-modern")
    assert extract_studio_template_id(with_meta) == "editorial-modern"
    assert visible_section_config(with_meta) == base
    cleared = inject_studio_template_id(with_meta, None)
    assert extract_studio_template_id(cleared) is None


def test_resolve_defaults_to_minimal_corporate():
    assert resolve_studio_template_id([]) == DEFAULT_STUDIO_TEMPLATE_ID
    assert resolve_studio_template_id([{"section_id": "skills", "enabled": True}]) == "minimal-corporate"
    cfg = inject_studio_template_id([], "government-ats")
    assert resolve_studio_template_id(cfg) == "government-ats"


def test_cv_generate_request_rejects_invalid_studio_template_id():
    with pytest.raises(ValidationError):
        CVGenerateRequest(studio_template_id="totally-fake-template")


def test_cv_generate_request_accepts_valid_studio_template_id():
    req = CVGenerateRequest(studio_template_id="project-portfolio", template="modern")
    assert req.studio_template_id == "project-portfolio"


def test_cv_update_request_rejects_invalid_studio_template_id():
    with pytest.raises(ValidationError):
        CVUpdateRequest(studio_template_id="nope")


def test_cv_read_hydrates_studio_template_id_from_section_config():
    data = {
        "id": "00000000-0000-0000-0000-000000000001",
        "user_id": "00000000-0000-0000-0000-000000000002",
        "target_job_id": None,
        "name": "Test CV",
        "template": "classic",
        "section_config": [
            {"section_id": "summary", "enabled": True},
            {"section_id": "_studio", "enabled": True, "studio_template_id": "bold-sidebar"},
        ],
        "rendered_content": {},
        "export_format_last_used": None,
        "created_at": "2026-07-12T00:00:00Z",
        "updated_at": "2026-07-12T00:00:00Z",
    }
    read = CVRead.model_validate(data)
    assert read.studio_template_id == "bold-sidebar"


def test_cv_read_missing_studio_meta_returns_none():
    data = {
        "id": "00000000-0000-0000-0000-000000000001",
        "user_id": "00000000-0000-0000-0000-000000000002",
        "name": "Old CV",
        "template": "modern",
        "section_config": [{"section_id": "summary", "enabled": True}],
        "rendered_content": {},
        "created_at": "2026-07-12T00:00:00Z",
        "updated_at": "2026-07-12T00:00:00Z",
    }
    read = CVRead.model_validate(data)
    assert read.studio_template_id is None


def test_taxonomy_meta_inject_extract_roundtrip_preserves_studio():
    from app.schemas.cv_builder import (
        CVTaxonomyMeta,
        content_section_config,
        extract_taxonomy_meta,
        inject_taxonomy_meta,
    )

    base = [
        {"section_id": "summary", "enabled": True},
        {"section_id": "_studio", "enabled": True, "studio_template_id": "bold-sidebar"},
    ]
    meta = CVTaxonomyMeta(
        target_role_text="Software Developer",
        matched_role_id="software_engineer",
        matched_skill_id=None,
        normalized_text="software developer",
        source="user_provided",
        confidence="suggested",
        explanation="Deterministic match from internal seed catalog.",
        accepted_by_user=False,
        kept_freeform=False,
        matched_role_title="Software Engineer",
    )
    with_tax = inject_taxonomy_meta(base, meta)
    assert extract_studio_template_id(with_tax) == "bold-sidebar"
    restored = extract_taxonomy_meta(with_tax)
    assert restored is not None
    assert restored.matched_role_id == "software_engineer"
    assert restored.target_role_text == "Software Developer"
    assert {"summary"} == {r["section_id"] for r in content_section_config(with_tax)}
    cleared = inject_taxonomy_meta(with_tax, None)
    assert extract_taxonomy_meta(cleared) is None
    assert extract_studio_template_id(cleared) == "bold-sidebar"


def test_cv_generate_and_update_accept_optional_taxonomy():
    from app.schemas.cv_builder import CVTaxonomyMeta

    tax = CVTaxonomyMeta(
        target_role_text="Electrical Engineer",
        matched_role_id="electrical_engineer",
        source="user_provided",
        confidence="suggested",
        accepted_by_user=True,
        kept_freeform=False,
    )
    gen = CVGenerateRequest(studio_template_id="minimal-corporate", taxonomy=tax)
    assert gen.taxonomy is not None
    assert gen.taxonomy.matched_role_id == "electrical_engineer"
    upd = CVUpdateRequest(taxonomy=tax, section_ids=["summary", "skills"])
    assert upd.taxonomy is not None
    assert upd.section_ids == ["summary", "skills"]


def test_filter_content_section_ids_drops_meta_rows():
    from app.schemas.cv_builder import filter_content_section_ids

    assert filter_content_section_ids(["summary", "_studio", "_taxonomy", "skills"]) == [
        "summary",
        "skills",
    ]
