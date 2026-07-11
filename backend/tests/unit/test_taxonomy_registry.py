"""
0051-F2 — Taxonomy registry MVP unit tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.taxonomy import (
    SEED_CATALOG,
    ConfidenceLevel,
    PathwayType,
    SourceType,
    TaxonomyRegistry,
    get_seed_catalog,
    validate_source_confidence,
)


TAXONOMY_ROOT = Path(__file__).resolve().parents[2] / "app" / "taxonomy"


@pytest.fixture
def registry() -> TaxonomyRegistry:
    return TaxonomyRegistry.from_seed_catalog()


def test_registry_loads_seed_catalog(registry: TaxonomyRegistry):
    assert get_seed_catalog() is SEED_CATALOG
    assert registry.get_role("software_engineer") is not None
    assert len(SEED_CATALOG.canonical_roles) >= 4
    assert len(SEED_CATALOG.skills) >= 4


def test_role_lookup_by_canonical_id(registry: TaxonomyRegistry):
    role = registry.get_role("software_engineer")
    assert role is not None
    assert role.title == "Software Engineer"
    assert registry.get_role("missing_role") is None


def test_role_match_by_title(registry: TaxonomyRegistry):
    match = registry.match_role("Software Engineer")
    assert match.matched_role_id == "software_engineer"
    assert match.matched_skill_id is None
    assert "title" in match.explanation


def test_role_match_by_alias_with_normalization(registry: TaxonomyRegistry):
    match = registry.match_role("  software   developer ")
    assert match.matched_role_id == "software_engineer"
    assert match.normalized_text == "software developer"
    assert "alias" in match.explanation


def test_unknown_role_returns_no_match_safely(registry: TaxonomyRegistry):
    match = registry.match_role("Chief Imagination Officer")
    assert match.matched_role_id is None
    assert match.matched_skill_id is None
    assert match.source == SourceType.UNKNOWN
    assert match.confidence == ConfidenceLevel.UNKNOWN
    assert "no deterministic seed match found" in match.explanation


def test_skill_lookup_by_id(registry: TaxonomyRegistry):
    skill = registry.get_skill("python")
    assert skill is not None
    assert skill.label == "Python"
    assert registry.get_skill("missing_skill") is None


def test_skill_match_by_label_and_alias(registry: TaxonomyRegistry):
    by_label = registry.match_skill("Python")
    assert by_label.matched_skill_id == "python"
    assert by_label.matched_role_id is None

    by_alias = registry.match_skill("  python3 ")
    assert by_alias.matched_skill_id == "python"
    assert "alias" in by_alias.explanation


def test_pathway_type_validation_accepts_valid_values(registry: TaxonomyRegistry):
    assert registry.validate_pathway_type("skill_gap") == PathwayType.SKILL_GAP
    assert registry.validate_pathway_type(PathwayType.CAREER_SWITCH) == PathwayType.CAREER_SWITCH
    assert len(registry.list_pathway_types()) == 11


def test_pathway_type_validation_rejects_invalid_values(registry: TaxonomyRegistry):
    with pytest.raises(ValueError, match="invalid pathway type"):
        registry.validate_pathway_type("warp_drive")


def test_skills_for_role_returns_seed_skills(registry: TaxonomyRegistry):
    skills = registry.skills_for_role("software_engineer")
    skill_ids = [s.id for s in skills]
    assert "python" in skill_ids
    # system_design is listed on the role but absent from seed skills — skipped safely
    assert "system_design" not in skill_ids
    assert registry.skills_for_role("missing_role") == []


def test_related_roles_is_deterministic_and_safe(registry: TaxonomyRegistry):
    related = registry.related_roles("software_engineer")
    assert [r.id for r in related] == ["project_manager"]
    assert registry.related_roles("electrical_engineer") == []
    assert registry.related_roles("missing_role") == []


def test_source_confidence_restrictions_enforced(registry: TaxonomyRegistry):
    with pytest.raises(ValueError, match="verified"):
        validate_source_confidence(SourceType.MODEL_INFERRED, ConfidenceLevel.VERIFIED)
    with pytest.raises(ValueError, match="verified"):
        validate_source_confidence(SourceType.USER_PROVIDED, ConfidenceLevel.VERIFIED)
    with pytest.raises(ValueError, match="verified"):
        validate_source_confidence(
            SourceType.EXTERNAL_TAXONOMY_REFERENCE, ConfidenceLevel.VERIFIED
        )

    coerced = registry.match_role(
        "SWE",
        source=SourceType.MODEL_INFERRED,
        confidence=ConfidenceLevel.VERIFIED,
    )
    assert coerced.matched_role_id == "software_engineer"
    assert coerced.confidence != ConfidenceLevel.VERIFIED
    assert coerced.confidence == ConfidenceLevel.INFERRED


def test_registry_modules_have_no_forbidden_runtime_imports():
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
        "import uvicorn",
        "from uvicorn",
        "import requests",
        "from requests",
        "import httpx",
        "from httpx",
    )
    py_files = sorted(TAXONOMY_ROOT.glob("*.py"))
    assert any(path.name == "registry.py" for path in py_files)
    for path in py_files:
        source = path.read_text(encoding="utf-8").lower()
        for snippet in forbidden_import_snippets:
            assert snippet.lower() not in source, f"{path.name} contains {snippet}"
