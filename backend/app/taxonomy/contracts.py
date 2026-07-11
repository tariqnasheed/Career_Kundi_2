"""
Taxonomy contract entities and enums (0051-F1).

Dependency-light Pydantic models + StrEnums. No database, FastAPI, or LLM imports.
"""

from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator

_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[_-][a-z0-9]+)*$")


def _validate_taxonomy_id(value: str) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        raise ValueError("id must be a non-empty lowercase kebab-case or snake_case string")
    if not _ID_PATTERN.fullmatch(cleaned):
        raise ValueError(
            "id must be lowercase kebab-case or snake_case "
            f"(got {value!r})"
        )
    return cleaned


def _normalize_alias_list(values: list[str]) -> list[str]:
    """Case-insensitive dedupe while preserving first-seen display form."""
    seen: set[str] = set()
    out: list[str] = []
    for raw in values or []:
        text = " ".join((raw or "").split()).strip()
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
    return out


class SourceType(StrEnum):
    USER_PROVIDED = "user_provided"
    PROFILE_SUPPORTED = "profile_supported"
    DOCUMENT_SUPPORTED = "document_supported"
    JOB_DESCRIPTION_SUPPORTED = "job_description_supported"
    EXTERNAL_TAXONOMY_REFERENCE = "external_taxonomy_reference"
    MODEL_INFERRED = "model_inferred"
    FALLBACK_DEFAULT = "fallback_default"
    UNKNOWN = "unknown"


class ConfidenceLevel(StrEnum):
    VERIFIED = "verified"
    EVIDENCE_BACKED = "evidence_backed"
    PROFILE_SUPPORTED = "profile_supported"
    SUGGESTED = "suggested"
    INFERRED = "inferred"
    DEFAULT = "default"
    UNKNOWN = "unknown"


class SeniorityLevel(StrEnum):
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    PRINCIPAL = "principal"
    MANAGER = "manager"
    DIRECTOR = "director"
    EXECUTIVE = "executive"
    UNKNOWN = "unknown"


class PathwayType(StrEnum):
    SKILL_GAP = "skill_gap"
    CAREER_SWITCH = "career_switch"
    GRADUATE_LAUNCH = "graduate_launch"
    INTERVIEW_PREPARATION = "interview_preparation"
    JOB_APPLICATION = "job_application"
    STUDY_EDUCATION = "study_education"
    PROFESSIONAL_CERTIFICATION = "professional_certification"
    PUBLIC_SECTOR = "public_sector"
    REGIONAL_READINESS = "regional_readiness"
    PORTFOLIO_PROJECT = "portfolio_project"
    PROMOTION_GROWTH = "promotion_growth"


class CareerDomain(BaseModel):
    id: str
    label: str = Field(min_length=1)
    description: str = ""
    aliases: list[str] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def _id(cls, value: str) -> str:
        return _validate_taxonomy_id(value)

    @field_validator("label")
    @classmethod
    def _label(cls, value: str) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            raise ValueError("label must be non-empty")
        return cleaned

    @field_validator("aliases")
    @classmethod
    def _aliases(cls, values: list[str]) -> list[str]:
        return _normalize_alias_list(values)


class RoleFamily(BaseModel):
    id: str
    domain_id: str
    label: str = Field(min_length=1)
    aliases: list[str] = Field(default_factory=list)
    example_roles: list[str] = Field(default_factory=list)

    @field_validator("id", "domain_id")
    @classmethod
    def _ids(cls, value: str) -> str:
        return _validate_taxonomy_id(value)

    @field_validator("label")
    @classmethod
    def _label(cls, value: str) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            raise ValueError("label must be non-empty")
        return cleaned

    @field_validator("aliases", "example_roles")
    @classmethod
    def _alias_lists(cls, values: list[str]) -> list[str]:
        return _normalize_alias_list(values)


class CanonicalRole(BaseModel):
    id: str
    role_family_id: str
    title: str = Field(min_length=1)
    aliases: list[str] = Field(default_factory=list)
    description: str = ""
    seniority_range: list[SeniorityLevel] = Field(default_factory=list)
    common_skills: list[str] = Field(default_factory=list)
    related_roles: list[str] = Field(default_factory=list)

    @field_validator("id", "role_family_id")
    @classmethod
    def _ids(cls, value: str) -> str:
        return _validate_taxonomy_id(value)

    @field_validator("title")
    @classmethod
    def _title(cls, value: str) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            raise ValueError("title must be non-empty")
        return cleaned

    @field_validator("aliases", "common_skills", "related_roles")
    @classmethod
    def _alias_lists(cls, values: list[str]) -> list[str]:
        return _normalize_alias_list(values)


class RoleAlias(BaseModel):
    alias: str = Field(min_length=1)
    canonical_role_id: str
    source: SourceType
    confidence: ConfidenceLevel

    @field_validator("canonical_role_id")
    @classmethod
    def _role_id(cls, value: str) -> str:
        return _validate_taxonomy_id(value)

    @field_validator("alias")
    @classmethod
    def _alias(cls, value: str) -> str:
        cleaned = " ".join((value or "").split()).strip()
        if not cleaned:
            raise ValueError("alias must be non-empty")
        return cleaned

    @model_validator(mode="after")
    def _source_confidence(self) -> RoleAlias:
        from app.taxonomy.normalization import validate_source_confidence

        validate_source_confidence(self.source, self.confidence)
        return self


class SkillCluster(BaseModel):
    id: str
    domain_id: str
    label: str = Field(min_length=1)
    aliases: list[str] = Field(default_factory=list)

    @field_validator("id", "domain_id")
    @classmethod
    def _ids(cls, value: str) -> str:
        return _validate_taxonomy_id(value)

    @field_validator("label")
    @classmethod
    def _label(cls, value: str) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            raise ValueError("label must be non-empty")
        return cleaned

    @field_validator("aliases")
    @classmethod
    def _aliases(cls, values: list[str]) -> list[str]:
        return _normalize_alias_list(values)


class Skill(BaseModel):
    id: str
    cluster_id: str
    label: str = Field(min_length=1)
    aliases: list[str] = Field(default_factory=list)
    evidence_examples: list[str] = Field(default_factory=list)
    tool_examples: list[str] = Field(default_factory=list)

    @field_validator("id", "cluster_id")
    @classmethod
    def _ids(cls, value: str) -> str:
        return _validate_taxonomy_id(value)

    @field_validator("label")
    @classmethod
    def _label(cls, value: str) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            raise ValueError("label must be non-empty")
        return cleaned

    @field_validator("aliases", "evidence_examples", "tool_examples")
    @classmethod
    def _lists(cls, values: list[str]) -> list[str]:
        return _normalize_alias_list(values)


class PathwayGoal(BaseModel):
    id: str
    pathway_type: PathwayType
    target_role_id: str
    goal_text: str = Field(min_length=1)
    source: SourceType
    confidence: ConfidenceLevel

    @field_validator("id", "target_role_id")
    @classmethod
    def _ids(cls, value: str) -> str:
        return _validate_taxonomy_id(value)

    @field_validator("goal_text")
    @classmethod
    def _goal(cls, value: str) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            raise ValueError("goal_text must be non-empty")
        return cleaned

    @model_validator(mode="after")
    def _source_confidence(self) -> PathwayGoal:
        from app.taxonomy.normalization import validate_source_confidence

        validate_source_confidence(self.source, self.confidence)
        return self


class TaxonomyMatch(BaseModel):
    """Deterministic match result for roles or skills (0051-F2).

    `matched_role_id` remains the role match field (F1 compat).
    `matched_skill_id` is set for skill matches; both stay None on no-match.
    """

    input_text: str
    normalized_text: str
    matched_role_id: str | None = None
    matched_skill_id: str | None = None
    source: SourceType
    confidence: ConfidenceLevel
    explanation: str = ""

    @field_validator("matched_role_id", "matched_skill_id")
    @classmethod
    def _optional_ids(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_taxonomy_id(value)

    @model_validator(mode="after")
    def _source_confidence(self) -> TaxonomyMatch:
        from app.taxonomy.normalization import validate_source_confidence

        validate_source_confidence(self.source, self.confidence)
        return self
