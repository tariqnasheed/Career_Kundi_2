"""
Passport HTTP request/response schemas (0052-F3).

Strict API models — not ORM models and not F1 domain contracts.
Unknown fields are rejected (extra=forbid).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.career_passport.contracts import (
    PassportCredentialType,
    PassportSectionKey,
    PassportSectionPreference,
    PassportTaxonomyReference,
)
from app.taxonomy.contracts import PathwayType, SeniorityLevel


class PassportApiModel(BaseModel):
    """Strict base for Passport HTTP schemas."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


# ---------------------------------------------------------------------------
# Record metadata (read-only in responses)
# ---------------------------------------------------------------------------


class PassportRecordMetaRead(PassportApiModel):
    source_status: str
    support_status: str
    verification_status: str


# ---------------------------------------------------------------------------
# Section preference (request + response reuse F1 type via validation)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Nested section reads
# ---------------------------------------------------------------------------


class PassportProfileRead(PassportApiModel):
    phone: str | None = None
    date_of_birth: date | None = None
    nationality: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    twitter_url: str | None = None
    other_social_links: list[dict[str, Any]] = Field(default_factory=list)
    address_city: str | None = None
    address_state: str | None = None
    address_country: str | None = None
    photo_url: str | None = None
    professional_headline: str | None = None
    bio_summary: str | None = None
    declaration_text: str | None = None
    references_available_on_request: bool = False
    interests: list[str] = Field(default_factory=list)
    record_meta: PassportRecordMetaRead


class PassportExperienceRead(PassportApiModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    job_title: str
    company_name: str
    company_url: str | None = None
    location: str | None = None
    employment_type: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    description_bullets: list[str] = Field(default_factory=list)
    order_index: int = 0
    role_taxonomy: PassportTaxonomyReference | None = None
    record_meta: PassportRecordMetaRead


class PassportEducationRead(PassportApiModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    degree: str
    field_of_study: str | None = None
    institution: str
    location: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    grade: str | None = None
    description_bullets: list[str] = Field(default_factory=list)
    relevant_coursework: list[str] = Field(default_factory=list)
    order_index: int = 0
    record_meta: PassportRecordMetaRead


class PassportProjectRead(PassportApiModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    title: str
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)
    project_url: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    role: str | None = None
    key_achievements: list[str] = Field(default_factory=list)
    order_index: int = 0
    skill_taxonomy: list[PassportTaxonomyReference] = Field(default_factory=list)
    record_meta: PassportRecordMetaRead


class PassportSkillRead(PassportApiModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    name: str
    skill_type: str = "technical"
    category: str | None = None
    proficiency: str | None = None
    order_index: int = 0
    taxonomy: PassportTaxonomyReference | None = None
    record_meta: PassportRecordMetaRead


class PassportCredentialRead(PassportApiModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    credential_type: PassportCredentialType
    name: str
    issuing_organization: str
    issue_date: date | None = None
    expiry_date: date | None = None
    credential_id: str | None = None
    credential_url: str | None = None
    order_index: int = 0
    record_meta: PassportRecordMetaRead


class PassportTargetRead(PassportApiModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    target_role_text: str
    role_taxonomy: PassportTaxonomyReference | None = None
    pathway_type: PathwayType | None = None
    target_country: str | None = None
    target_region: str | None = None
    target_industry: str | None = None
    target_seniority: SeniorityLevel | None = None
    time_horizon: str | None = None
    priority: int = 3
    order_index: int = 0
    record_meta: PassportRecordMetaRead


class PassportRead(PassportApiModel):
    id: UUID
    subject_id: UUID | None = None
    display_name: str | None = None
    headline: str | None = None
    summary: str | None = None
    visibility: str
    version: int
    section_preferences: list[PassportSectionPreference]
    profile: PassportProfileRead
    experiences: list[PassportExperienceRead] = Field(default_factory=list)
    education: list[PassportEducationRead] = Field(default_factory=list)
    projects: list[PassportProjectRead] = Field(default_factory=list)
    skills: list[PassportSkillRead] = Field(default_factory=list)
    credentials: list[PassportCredentialRead] = Field(default_factory=list)
    targets: list[PassportTargetRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class PassportEnvelope(PassportApiModel):
    data: PassportRead


# ---------------------------------------------------------------------------
# Aggregate / profile patches
# ---------------------------------------------------------------------------


def _validate_section_preferences(
    prefs: list[PassportSectionPreference],
) -> list[PassportSectionPreference]:
    if len(prefs) != 7:
        raise ValueError("section_preferences must contain exactly seven entries")
    sections = [p.section for p in prefs]
    if len(set(sections)) != 7:
        raise ValueError("section_preferences must include each section exactly once")
    expected = set(PassportSectionKey)
    if set(sections) != expected:
        raise ValueError("section_preferences must include every PassportSectionKey")
    indexes = sorted(p.order_index for p in prefs)
    if indexes != list(range(7)):
        raise ValueError("section_preferences order_index values must be exactly 0..6")
    return prefs


class PassportPatch(PassportApiModel):
    expected_version: int = Field(ge=1)
    subject_id: UUID | None = None
    section_preferences: list[PassportSectionPreference] | None = None

    @model_validator(mode="after")
    def _rules(self) -> PassportPatch:
        mutable = self.model_fields_set - {"expected_version"}
        if not mutable:
            raise ValueError("At least one mutable field is required besides expected_version")
        if self.section_preferences is not None:
            _validate_section_preferences(self.section_preferences)
        return self


_PROFILE_PATCH_FIELDS = frozenset(
    {
        "phone",
        "date_of_birth",
        "nationality",
        "linkedin_url",
        "github_url",
        "portfolio_url",
        "twitter_url",
        "other_social_links",
        "address_city",
        "address_state",
        "address_country",
        "photo_url",
        "professional_headline",
        "bio_summary",
        "declaration_text",
        "references_available_on_request",
        "interests",
    }
)


class PassportProfilePatch(PassportApiModel):
    expected_version: int = Field(ge=1)
    phone: str | None = None
    date_of_birth: date | None = None
    nationality: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    twitter_url: str | None = None
    other_social_links: list[dict[str, Any]] | None = None
    address_city: str | None = None
    address_state: str | None = None
    address_country: str | None = None
    photo_url: str | None = None
    professional_headline: str | None = None
    bio_summary: str | None = None
    declaration_text: str | None = None
    references_available_on_request: bool | None = None
    interests: list[str] | None = None

    @model_validator(mode="after")
    def _at_least_one(self) -> PassportProfilePatch:
        if not (self.model_fields_set & _PROFILE_PATCH_FIELDS):
            raise ValueError("At least one Profile field is required besides expected_version")
        return self


# ---------------------------------------------------------------------------
# Section create / patch
# ---------------------------------------------------------------------------


class PassportExperienceCreate(PassportApiModel):
    expected_version: int = Field(ge=1)
    job_title: str
    company_name: str
    company_url: str | None = None
    location: str | None = None
    employment_type: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    description_bullets: list[str] = Field(default_factory=list)
    order_index: int = 0
    role_taxonomy: PassportTaxonomyReference | None = None


class PassportExperiencePatch(PassportApiModel):
    expected_version: int = Field(ge=1)
    job_title: str | None = None
    company_name: str | None = None
    company_url: str | None = None
    location: str | None = None
    employment_type: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None
    description_bullets: list[str] | None = None
    order_index: int | None = None
    role_taxonomy: PassportTaxonomyReference | None = None

    @model_validator(mode="after")
    def _at_least_one(self) -> PassportExperiencePatch:
        if not (self.model_fields_set - {"expected_version"}):
            raise ValueError("At least one mutable field is required")
        return self


class PassportEducationCreate(PassportApiModel):
    expected_version: int = Field(ge=1)
    degree: str
    field_of_study: str | None = None
    institution: str
    location: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    grade: str | None = None
    description_bullets: list[str] = Field(default_factory=list)
    relevant_coursework: list[str] = Field(default_factory=list)
    order_index: int = 0


class PassportEducationPatch(PassportApiModel):
    expected_version: int = Field(ge=1)
    degree: str | None = None
    field_of_study: str | None = None
    institution: str | None = None
    location: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None
    grade: str | None = None
    description_bullets: list[str] | None = None
    relevant_coursework: list[str] | None = None
    order_index: int | None = None

    @model_validator(mode="after")
    def _at_least_one(self) -> PassportEducationPatch:
        if not (self.model_fields_set - {"expected_version"}):
            raise ValueError("At least one mutable field is required")
        return self


class PassportProjectCreate(PassportApiModel):
    expected_version: int = Field(ge=1)
    title: str
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)
    project_url: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    role: str | None = None
    key_achievements: list[str] = Field(default_factory=list)
    order_index: int = 0
    skill_taxonomy: list[PassportTaxonomyReference] = Field(default_factory=list)


class PassportProjectPatch(PassportApiModel):
    expected_version: int = Field(ge=1)
    title: str | None = None
    description: str | None = None
    technologies: list[str] | None = None
    project_url: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    role: str | None = None
    key_achievements: list[str] | None = None
    order_index: int | None = None
    skill_taxonomy: list[PassportTaxonomyReference] | None = None

    @model_validator(mode="after")
    def _at_least_one(self) -> PassportProjectPatch:
        if not (self.model_fields_set - {"expected_version"}):
            raise ValueError("At least one mutable field is required")
        return self


class PassportSkillCreate(PassportApiModel):
    expected_version: int = Field(ge=1)
    name: str
    skill_type: str = "technical"
    category: str | None = None
    proficiency: str | None = None
    order_index: int = 0
    taxonomy: PassportTaxonomyReference | None = None


class PassportSkillPatch(PassportApiModel):
    expected_version: int = Field(ge=1)
    name: str | None = None
    skill_type: str | None = None
    category: str | None = None
    proficiency: str | None = None
    order_index: int | None = None
    taxonomy: PassportTaxonomyReference | None = None

    @model_validator(mode="after")
    def _at_least_one(self) -> PassportSkillPatch:
        if not (self.model_fields_set - {"expected_version"}):
            raise ValueError("At least one mutable field is required")
        return self


class PassportCredentialCreate(PassportApiModel):
    expected_version: int = Field(ge=1)
    credential_type: PassportCredentialType = PassportCredentialType.CERTIFICATION
    name: str
    issuing_organization: str
    issue_date: date | None = None
    expiry_date: date | None = None
    credential_id: str | None = None
    credential_url: str | None = None
    order_index: int = 0


class PassportCredentialPatch(PassportApiModel):
    expected_version: int = Field(ge=1)
    credential_type: PassportCredentialType | None = None
    name: str | None = None
    issuing_organization: str | None = None
    issue_date: date | None = None
    expiry_date: date | None = None
    credential_id: str | None = None
    credential_url: str | None = None
    order_index: int | None = None

    @model_validator(mode="after")
    def _at_least_one(self) -> PassportCredentialPatch:
        if not (self.model_fields_set - {"expected_version"}):
            raise ValueError("At least one mutable field is required")
        return self


class PassportTargetCreate(PassportApiModel):
    expected_version: int = Field(ge=1)
    target_role_text: str
    role_taxonomy: PassportTaxonomyReference | None = None
    pathway_type: PathwayType | None = None
    target_country: str | None = None
    target_region: str | None = None
    target_industry: str | None = None
    target_seniority: SeniorityLevel | None = None
    time_horizon: str | None = None
    priority: int = 3
    order_index: int = 0


class PassportTargetPatch(PassportApiModel):
    expected_version: int = Field(ge=1)
    target_role_text: str | None = None
    role_taxonomy: PassportTaxonomyReference | None = None
    pathway_type: PathwayType | None = None
    target_country: str | None = None
    target_region: str | None = None
    target_industry: str | None = None
    target_seniority: SeniorityLevel | None = None
    time_horizon: str | None = None
    priority: int | None = None
    order_index: int | None = None

    @model_validator(mode="after")
    def _at_least_one(self) -> PassportTargetPatch:
        if not (self.model_fields_set - {"expected_version"}):
            raise ValueError("At least one mutable field is required")
        return self


class PassportReorder(PassportApiModel):
    expected_version: int = Field(ge=1)
    ordered_ids: list[UUID]

    @model_validator(mode="after")
    def _no_duplicates(self) -> PassportReorder:
        if len(self.ordered_ids) != len(set(self.ordered_ids)):
            raise ValueError("ordered_ids must not contain duplicates")
        return self
