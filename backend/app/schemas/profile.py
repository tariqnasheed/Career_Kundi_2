"""
schemas/profile.py
======================
Pydantic schemas for the Profile Data Hub (§4.4). One schema pair
(`<Thing>Create`/`<Thing>Read`) per repeatable section, plus `ProfileRead`
which nests all of them — this is the exact payload shape the CV Builder's
"Dynamic Section Toggles" panel consumes to know which sections have data.
"""

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class _ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class EducationIn(BaseModel):
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


class EducationOut(EducationIn, _ORMModel):
    id: uuid.UUID


class WorkExperienceIn(BaseModel):
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


class WorkExperienceOut(WorkExperienceIn, _ORMModel):
    id: uuid.UUID


class ProjectIn(BaseModel):
    title: str
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)
    project_url: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    role: str | None = None
    key_achievements: list[str] = Field(default_factory=list)
    order_index: int = 0


class ProjectOut(ProjectIn, _ORMModel):
    id: uuid.UUID


class CertificationIn(BaseModel):
    name: str
    issuing_organization: str
    issue_date: date | None = None
    expiry_date: date | None = None
    credential_id: str | None = None
    credential_url: str | None = None
    order_index: int = 0


class CertificationOut(CertificationIn, _ORMModel):
    id: uuid.UUID


class PublicationIn(BaseModel):
    title: str
    publisher: str | None = None
    publication_date: date | None = None
    url: str | None = None
    co_authors: list[str] = Field(default_factory=list)
    abstract: str | None = None
    order_index: int = 0


class PublicationOut(PublicationIn, _ORMModel):
    id: uuid.UUID


class LanguageIn(BaseModel):
    name: str
    proficiency: str
    order_index: int = 0


class LanguageOut(LanguageIn, _ORMModel):
    id: uuid.UUID


class VolunteerIn(BaseModel):
    role: str
    organization: str
    cause_area: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    description_bullets: list[str] = Field(default_factory=list)
    order_index: int = 0


class VolunteerOut(VolunteerIn, _ORMModel):
    id: uuid.UUID


class AwardIn(BaseModel):
    name: str
    issuing_organization: str | None = None
    date_received: date | None = None
    description: str | None = None
    order_index: int = 0


class AwardOut(AwardIn, _ORMModel):
    id: uuid.UUID


class ReferenceIn(BaseModel):
    name: str
    title: str | None = None
    organization: str | None = None
    email: str | None = None
    phone: str | None = None
    relationship_to_user: str | None = None
    order_index: int = 0


class ReferenceOut(ReferenceIn, _ORMModel):
    id: uuid.UUID


class SkillIn(BaseModel):
    name: str
    skill_type: str = "technical"
    category: str | None = None
    proficiency: str | None = None
    order_index: int = 0


class SkillOut(SkillIn, _ORMModel):
    id: uuid.UUID


class CustomSectionEntryIn(BaseModel):
    entry_title: str
    subtitle: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    description_bullets: list[str] = Field(default_factory=list)
    order_index: int = 0


class CustomSectionEntryOut(CustomSectionEntryIn, _ORMModel):
    id: uuid.UUID


class CustomSectionIn(BaseModel):
    title: str
    section_type: str = "list"  # list | free_text | tags
    free_text_content: str | None = None
    tags: list[str] = Field(default_factory=list)
    order_index: int = 0


class CustomSectionOut(CustomSectionIn, _ORMModel):
    id: uuid.UUID
    entries: list[CustomSectionEntryOut] = Field(default_factory=list)


class ProfileUpdate(BaseModel):
    """Partial-update payload for top-level Personal Information fields."""

    phone: str | None = None
    date_of_birth: date | None = None
    nationality: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    twitter_url: str | None = None
    other_social_links: list[dict] | None = None
    address_city: str | None = None
    address_state: str | None = None
    address_country: str | None = None
    photo_url: str | None = None
    professional_headline: str | None = None
    bio_summary: str | None = Field(default=None, max_length=1000)
    declaration_text: str | None = None
    references_available_on_request: bool | None = None
    interests: list[str] | None = None


class ProfileRead(_ORMModel):
    id: uuid.UUID
    phone: str | None
    date_of_birth: date | None
    nationality: str | None
    linkedin_url: str | None
    github_url: str | None
    portfolio_url: str | None
    twitter_url: str | None
    other_social_links: list
    address_city: str | None
    address_state: str | None
    address_country: str | None
    photo_url: str | None
    professional_headline: str | None
    bio_summary: str | None
    declaration_text: str | None
    references_available_on_request: bool
    interests: list

    educations: list[EducationOut] = Field(default_factory=list)
    work_experiences: list[WorkExperienceOut] = Field(default_factory=list)
    projects: list[ProjectOut] = Field(default_factory=list)
    certifications: list[CertificationOut] = Field(default_factory=list)
    publications: list[PublicationOut] = Field(default_factory=list)
    languages: list[LanguageOut] = Field(default_factory=list)
    volunteer_entries: list[VolunteerOut] = Field(default_factory=list)
    awards: list[AwardOut] = Field(default_factory=list)
    references: list[ReferenceOut] = Field(default_factory=list)
    skills: list[SkillOut] = Field(default_factory=list)
    custom_sections: list[CustomSectionOut] = Field(default_factory=list)

    completeness_score: float = 0.0
