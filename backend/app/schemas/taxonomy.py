"""
Taxonomy API request/response schemas (0051-F4).

Read-only DTOs over the in-memory taxonomy registry. No ORM / DB coupling.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.taxonomy.contracts import ConfidenceLevel, SourceType


class TaxonomyHealthRead(BaseModel):
    available: bool
    catalog_name: str
    domain_count: int
    role_count: int
    skill_count: int
    pathway_type_count: int
    external_dataset_ingestion: bool


class TaxonomyPathwayTypeRead(BaseModel):
    id: str
    label: str
    description: str | None = None


class TaxonomyMatchRequest(BaseModel):
    input_text: str = Field(min_length=1)
    source: SourceType | None = None
    confidence: ConfidenceLevel | None = None

    @field_validator("input_text")
    @classmethod
    def _trim_input(cls, value: str) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            raise ValueError("input_text must be non-empty after trim")
        return cleaned


class TaxonomyMatchRead(BaseModel):
    input_text: str
    normalized_text: str
    matched_role_id: str | None = None
    matched_skill_id: str | None = None
    source: SourceType
    confidence: ConfidenceLevel
    explanation: str = ""


class TaxonomyRoleRead(BaseModel):
    id: str
    title: str
    aliases: list[str] = Field(default_factory=list)
    description: str = ""
    common_skills: list[str] = Field(default_factory=list)
    related_roles: list[str] = Field(default_factory=list)
    source: SourceType
    confidence: ConfidenceLevel


class TaxonomySkillRead(BaseModel):
    id: str
    label: str
    aliases: list[str] = Field(default_factory=list)
    evidence_examples: list[str] = Field(default_factory=list)
    tool_examples: list[str] = Field(default_factory=list)
    source: SourceType
    confidence: ConfidenceLevel


class TaxonomyRoleSkillsRead(BaseModel):
    role_id: str
    skills: list[TaxonomySkillRead] = Field(default_factory=list)


class TaxonomyRelatedRolesRead(BaseModel):
    role_id: str
    related_roles: list[TaxonomyRoleRead] = Field(default_factory=list)


class TaxonomyErrorRead(BaseModel):
    message: str
    code: str
