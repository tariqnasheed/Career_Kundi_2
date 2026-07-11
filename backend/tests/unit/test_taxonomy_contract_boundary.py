"""
0051-F1 — Taxonomy contract boundary unit tests.

Covers enums, normalization, validation guards, seed catalog shape, and
import-boundary hygiene for the pure taxonomy package.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.taxonomy import (
    SEED_CATALOG,
    CanonicalRole,
    CareerDomain,
    ConfidenceLevel,
    PathwayType,
    SourceType,
    build_taxonomy_match,
    get_seed_catalog,
    normalize_aliases,
    normalize_taxonomy_text,
    safe_default_source,
    validate_source_confidence,
)
from app.taxonomy.contracts import SeniorityLevel


TAXONOMY_ROOT = Path(__file__).resolve().parents[2] / "app" / "taxonomy"


def test_source_type_values_include_required_labels():
    expected = {
        "user_provided",
        "profile_supported",
        "document_supported",
        "job_description_supported",
        "external_taxonomy_reference",
        "model_inferred",
        "fallback_default",
        "unknown",
    }
    assert {member.value for member in SourceType} == expected


def test_pathway_type_values_include_all_eleven():
    expected = {
        "skill_gap",
        "career_switch",
        "graduate_launch",
        "interview_preparation",
        "job_application",
        "study_education",
        "professional_certification",
        "public_sector",
        "regional_readiness",
        "portfolio_project",
        "promotion_growth",
    }
    assert {member.value for member in PathwayType} == expected
    assert len(PathwayType) == 11


def test_normalize_taxonomy_text_trims_collapses_and_lowercases():
    assert normalize_taxonomy_text("  Software   Engineer  ") == "software engineer"
    assert normalize_taxonomy_text("Project\tManager") == "project manager"


def test_normalize_aliases_deduplicates_case_insensitively():
    assert normalize_aliases(["PM", "pm", "  Project Manager ", "PM", ""]) == [
        "PM",
        "Project Manager",
    ]


def test_invalid_empty_entity_id_is_rejected():
    with pytest.raises(ValidationError):
        CareerDomain(id="", label="Technology")
    with pytest.raises(ValidationError):
        CanonicalRole(id=" ", role_family_id="software_engineering", title="Software Engineer")


def test_model_inferred_cannot_be_verified():
    with pytest.raises(ValueError, match="model_inferred"):
        validate_source_confidence(SourceType.MODEL_INFERRED, ConfidenceLevel.VERIFIED)


def test_fallback_default_cannot_be_verified():
    with pytest.raises(ValueError, match="fallback_default"):
        validate_source_confidence(SourceType.FALLBACK_DEFAULT, ConfidenceLevel.VERIFIED)


def test_unknown_source_defaults_to_unknown_confidence():
    assert safe_default_source(None) == SourceType.UNKNOWN
    assert safe_default_source("   ") == SourceType.UNKNOWN
    with pytest.raises(ValueError, match="unknown source"):
        validate_source_confidence(SourceType.UNKNOWN, ConfidenceLevel.SUGGESTED)
    match = build_taxonomy_match(
        input_text="",
        matched_role_id=None,
        source=SourceType.UNKNOWN,
        confidence=ConfidenceLevel.SUGGESTED,
        explanation="empty input",
    )
    assert match.confidence == ConfidenceLevel.UNKNOWN


def test_seed_catalog_contains_representative_domains_roles_skills():
    catalog = get_seed_catalog()
    assert catalog is SEED_CATALOG
    domain_ids = {d.id for d in catalog.domains}
    role_ids = {r.id for r in catalog.canonical_roles}
    skill_ids = {s.id for s in catalog.skills}
    cluster_ids = {c.id for c in catalog.skill_clusters}

    assert {"technology", "engineering", "healthcare", "business_operations"} <= domain_ids
    assert {
        "software_engineer",
        "electrical_engineer",
        "clinical_pharmacist",
        "project_manager",
    } <= role_ids
    assert {
        "programming",
        "electrical_design",
        "clinical_safety",
        "delivery_management",
    } <= cluster_ids
    assert {
        "python",
        "load_calculations",
        "medication_safety",
        "stakeholder_coordination",
    } <= skill_ids
    assert SeniorityLevel.MID in catalog.canonical_roles[0].seniority_range


def test_build_taxonomy_match_returns_non_verified_for_inferred_data():
    match = build_taxonomy_match(
        input_text="  SoftWare   Engineer ",
        matched_role_id="software_engineer",
        source=SourceType.MODEL_INFERRED,
        confidence=ConfidenceLevel.VERIFIED,
        explanation="heuristic guess",
    )
    assert match.normalized_text == "software engineer"
    assert match.matched_role_id == "software_engineer"
    assert match.source == SourceType.MODEL_INFERRED
    assert match.confidence != ConfidenceLevel.VERIFIED
    assert match.confidence == ConfidenceLevel.INFERRED


def test_taxonomy_modules_have_no_forbidden_runtime_imports():
    """Import-boundary sanity: reject real dependency imports, not incidental words."""
    forbidden_import_snippets = (
        "from fastapi",
        "import fastapi",
        "from sqlalchemy",
        "import sqlalchemy",
        "from openai",
        "import openai",
        "from anthropic",
        "import anthropic",
        "google.generativeai",
        "ChatOpenAI",
        "ChatGoogle",
        "APIRouter",
        "Session(",
    )
    py_files = sorted(TAXONOMY_ROOT.glob("*.py"))
    assert py_files, "expected taxonomy package files"
    for path in py_files:
        source = path.read_text(encoding="utf-8")
        lowered = source.lower()
        for snippet in forbidden_import_snippets:
            assert snippet.lower() not in lowered, f"{path.name} contains forbidden import marker: {snippet}"
