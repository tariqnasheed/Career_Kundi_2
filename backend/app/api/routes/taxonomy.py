"""
Read-only Taxonomy API (0051-F4).

Exposes the in-memory TaxonomyRegistry under /api/v1/taxonomy.
No DB session, no external HTTP, no LLM calls, no writes.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.core.errors import NotFoundError, ValidationFailedError
from app.db.models.user import User
from app.schemas.taxonomy import (
    TaxonomyHealthRead,
    TaxonomyMatchRead,
    TaxonomyMatchRequest,
    TaxonomyPathwayTypeRead,
    TaxonomyRelatedRolesRead,
    TaxonomyRoleRead,
    TaxonomyRoleSkillsRead,
    TaxonomySkillRead,
)
from app.taxonomy import SEED_CATALOG, ConfidenceLevel, PathwayType, SourceType, TaxonomyRegistry
from app.taxonomy.contracts import CanonicalRole, Skill
from app.taxonomy.normalization import validate_source_confidence

router = APIRouter(prefix="/taxonomy", tags=["taxonomy"])

_registry = TaxonomyRegistry.from_seed_catalog()

_PATHWAY_META: dict[PathwayType, tuple[str, str]] = {
    PathwayType.SKILL_GAP: ("Skill Gap Plan", "Close skill gaps toward a target role."),
    PathwayType.CAREER_SWITCH: ("Career Switch Plan", "Transfer into a new role family."),
    PathwayType.GRADUATE_LAUNCH: ("Graduate Launch Plan", "First-role readiness after study."),
    PathwayType.INTERVIEW_PREPARATION: (
        "Interview Preparation Path",
        "Prepare evidence-backed interview readiness.",
    ),
    PathwayType.JOB_APPLICATION: ("Job Application Path", "Structure application readiness."),
    PathwayType.STUDY_EDUCATION: (
        "Study / Education Path",
        "Plan education or study-abroad readiness.",
    ),
    PathwayType.PROFESSIONAL_CERTIFICATION: (
        "Professional Certification Path",
        "Plan certification preparation with official-source verification later.",
    ),
    PathwayType.PUBLIC_SECTOR: ("Public Sector Path", "Public hiring readiness checklist."),
    PathwayType.REGIONAL_READINESS: (
        "Regional Readiness Path",
        "Regional or mobility readiness with caveats.",
    ),
    PathwayType.PORTFOLIO_PROJECT: ("Portfolio / Project Path", "Build proof-of-skill projects."),
    PathwayType.PROMOTION_GROWTH: (
        "Promotion / Seniority Growth Path",
        "Grow seniority within a role family.",
    ),
}

# Seed catalog is internal/illustrative — never present as verified external taxonomy.
_SEED_SOURCE = SourceType.EXTERNAL_TAXONOMY_REFERENCE
_SEED_CONFIDENCE = ConfidenceLevel.SUGGESTED


def get_taxonomy_registry() -> TaxonomyRegistry:
    return _registry


def _role_read(role: CanonicalRole) -> TaxonomyRoleRead:
    return TaxonomyRoleRead(
        id=role.id,
        title=role.title,
        aliases=list(role.aliases),
        description=role.description,
        common_skills=list(role.common_skills),
        related_roles=list(role.related_roles),
        source=_SEED_SOURCE,
        confidence=_SEED_CONFIDENCE,
    )


def _skill_read(skill: Skill) -> TaxonomySkillRead:
    return TaxonomySkillRead(
        id=skill.id,
        label=skill.label,
        aliases=list(skill.aliases),
        evidence_examples=list(skill.evidence_examples),
        tool_examples=list(skill.tool_examples),
        source=_SEED_SOURCE,
        confidence=_SEED_CONFIDENCE,
    )


def _match_read(match) -> TaxonomyMatchRead:
    return TaxonomyMatchRead(
        input_text=match.input_text,
        normalized_text=match.normalized_text,
        matched_role_id=match.matched_role_id,
        matched_skill_id=match.matched_skill_id,
        source=match.source,
        confidence=match.confidence,
        explanation=match.explanation,
    )


def _match_kwargs(payload: TaxonomyMatchRequest) -> dict:
    if payload.source is not None and payload.confidence is not None:
        try:
            validate_source_confidence(payload.source, payload.confidence)
        except ValueError as exc:
            raise ValidationFailedError(str(exc)) from exc
    kwargs: dict = {}
    if payload.source is not None:
        kwargs["source"] = payload.source
    if payload.confidence is not None:
        kwargs["confidence"] = payload.confidence
    return kwargs


@router.get("/health", response_model=TaxonomyHealthRead)
async def taxonomy_health() -> TaxonomyHealthRead:
    """Public read-only health for taxonomy registry availability (no auth)."""
    catalog = SEED_CATALOG
    return TaxonomyHealthRead(
        available=True,
        catalog_name="internal_seed",
        domain_count=len(catalog.domains),
        role_count=len(catalog.canonical_roles),
        skill_count=len(catalog.skills),
        pathway_type_count=len(PathwayType),
        external_dataset_ingestion=False,
    )


@router.get("/pathway-types", response_model=list[TaxonomyPathwayTypeRead])
async def list_pathway_types(
    _user: User = Depends(get_current_user),
    registry: TaxonomyRegistry = Depends(get_taxonomy_registry),
) -> list[TaxonomyPathwayTypeRead]:
    out: list[TaxonomyPathwayTypeRead] = []
    for pathway in registry.list_pathway_types():
        label, description = _PATHWAY_META[pathway]
        out.append(
            TaxonomyPathwayTypeRead(id=pathway.value, label=label, description=description)
        )
    return out


@router.post("/roles/match", response_model=TaxonomyMatchRead)
async def match_role(
    payload: TaxonomyMatchRequest,
    _user: User = Depends(get_current_user),
    registry: TaxonomyRegistry = Depends(get_taxonomy_registry),
) -> TaxonomyMatchRead:
    return _match_read(registry.match_role(payload.input_text, **_match_kwargs(payload)))


@router.post("/skills/match", response_model=TaxonomyMatchRead)
async def match_skill(
    payload: TaxonomyMatchRequest,
    _user: User = Depends(get_current_user),
    registry: TaxonomyRegistry = Depends(get_taxonomy_registry),
) -> TaxonomyMatchRead:
    return _match_read(registry.match_skill(payload.input_text, **_match_kwargs(payload)))


@router.get("/roles/{role_id}", response_model=TaxonomyRoleRead)
async def get_role(
    role_id: str,
    _user: User = Depends(get_current_user),
    registry: TaxonomyRegistry = Depends(get_taxonomy_registry),
) -> TaxonomyRoleRead:
    role = registry.get_role(role_id)
    if role is None:
        raise NotFoundError("Taxonomy role not found.")
    return _role_read(role)


@router.get("/roles/{role_id}/skills", response_model=TaxonomyRoleSkillsRead)
async def get_role_skills(
    role_id: str,
    _user: User = Depends(get_current_user),
    registry: TaxonomyRegistry = Depends(get_taxonomy_registry),
) -> TaxonomyRoleSkillsRead:
    if registry.get_role(role_id) is None:
        raise NotFoundError("Taxonomy role not found.")
    skills = registry.skills_for_role(role_id)
    return TaxonomyRoleSkillsRead(role_id=role_id, skills=[_skill_read(s) for s in skills])


@router.get("/roles/{role_id}/related", response_model=TaxonomyRelatedRolesRead)
async def get_related_roles(
    role_id: str,
    _user: User = Depends(get_current_user),
    registry: TaxonomyRegistry = Depends(get_taxonomy_registry),
) -> TaxonomyRelatedRolesRead:
    if registry.get_role(role_id) is None:
        raise NotFoundError("Taxonomy role not found.")
    related = registry.related_roles(role_id)
    return TaxonomyRelatedRolesRead(
        role_id=role_id,
        related_roles=[_role_read(r) for r in related],
    )
