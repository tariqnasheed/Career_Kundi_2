"""
Universal Role & Pathway Taxonomy — contract boundary (0051-F1).

Pure, deterministic types and helpers. No DB, FastAPI routes, LLM clients,
or feature integrations in this package.
"""

from __future__ import annotations

from app.taxonomy.catalog import SEED_CATALOG, get_seed_catalog
from app.taxonomy.contracts import (
    CanonicalRole,
    CareerDomain,
    ConfidenceLevel,
    PathwayGoal,
    PathwayType,
    RoleAlias,
    RoleFamily,
    SeniorityLevel,
    Skill,
    SkillCluster,
    SourceType,
    TaxonomyMatch,
)
from app.taxonomy.normalization import (
    build_taxonomy_match,
    normalize_aliases,
    normalize_taxonomy_text,
    safe_default_source,
    validate_source_confidence,
)

__all__ = [
    "SEED_CATALOG",
    "CanonicalRole",
    "CareerDomain",
    "ConfidenceLevel",
    "PathwayGoal",
    "PathwayType",
    "RoleAlias",
    "RoleFamily",
    "SeniorityLevel",
    "Skill",
    "SkillCluster",
    "SourceType",
    "TaxonomyMatch",
    "build_taxonomy_match",
    "get_seed_catalog",
    "normalize_aliases",
    "normalize_taxonomy_text",
    "safe_default_source",
    "validate_source_confidence",
]
