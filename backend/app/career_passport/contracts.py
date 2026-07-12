"""
Career & Education Passport — logical domain contracts (0052-F1).

These are logical domain contracts, not ORM models and not HTTP request schemas.
F2 decides persistence mapping.
F3 decides API request/response schemas.

No database, FastAPI, SQLAlchemy, LLM providers, or feature integrations.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.platform.claims.status import SupportStatus, VerificationStatus
from app.taxonomy.contracts import (
    ConfidenceLevel,
    PathwayType,
    SeniorityLevel,
    SourceType,
    _validate_taxonomy_id,
)
from app.taxonomy.normalization import normalize_taxonomy_text, validate_source_confidence


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class PassportContractModel(BaseModel):
    """Strict base for all Passport contract models."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=False,
    )


# ---------------------------------------------------------------------------
# Enums (Passport-owned)
# ---------------------------------------------------------------------------


class PassportVisibility(StrEnum):
    PRIVATE = "private"


class PassportSectionKey(StrEnum):
    PROFILE = "profile"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    PROJECTS = "projects"
    SKILLS = "skills"
    CREDENTIALS = "credentials"
    TARGETS = "targets"


class PassportSourceStatus(StrEnum):
    USER_ASSERTED = "user_asserted"
    SUGGESTED_ACCEPTED = "suggested_accepted"
    UNKNOWN = "unknown"
    NOT_PROVIDED = "not_provided"


class PassportTaxonomyKind(StrEnum):
    ROLE = "role"
    SKILL = "skill"


class PassportCredentialType(StrEnum):
    CERTIFICATION = "certification"
    LICENSE = "license"
    COURSE_CERTIFICATE = "course_certificate"
    EDUCATION_AWARD = "education_award"
    PROFESSIONAL_MEMBERSHIP = "professional_membership"
    OTHER = "other"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _normalize_string_list(values: list[str] | None) -> list[str]:
    """Trim, drop blanks, case-insensitive dedupe; preserve first-seen display form."""
    seen: set[str] = set()
    out: list[str] = []
    for raw in values or []:
        text = " ".join(str(raw or "").split()).strip()
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
    return out


def _require_nonblank(value: str, field_name: str) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        raise ValueError(f"{field_name} must be non-empty")
    return cleaned


def _validate_date_order(
    start: date | None,
    end: date | None,
    *,
    is_current: bool = False,
) -> None:
    if is_current and end is not None:
        raise ValueError("end_date must be None when is_current is true")
    if start is not None and end is not None and end < start:
        raise ValueError("end_date must be on or after start_date")


def _assert_taxonomy_kind(
    ref: PassportTaxonomyReference | None,
    expected: PassportTaxonomyKind,
    field_name: str,
) -> None:
    if ref is None:
        return
    if ref.kind != expected:
        raise ValueError(f"{field_name} taxonomy kind must be {expected.value}")


# ---------------------------------------------------------------------------
# Record metadata
# ---------------------------------------------------------------------------


_ALLOWED_SUPPORT = frozenset({SupportStatus.NOT_PROVIDED, SupportStatus.PROFILE_SUPPORTED})
_FORBIDDEN_VERIFICATION = frozenset(
    {
        VerificationStatus.VERIFIED,
        VerificationStatus.REJECTED,
        VerificationStatus.CONFLICTING,
        VerificationStatus.UNKNOWN,
    }
)


class PassportRecordMeta(PassportContractModel):
    """Reduced Passport subset of claim status axes — not a full Claim row."""

    source_status: PassportSourceStatus = PassportSourceStatus.USER_ASSERTED
    support_status: SupportStatus = SupportStatus.NOT_PROVIDED
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED

    @model_validator(mode="after")
    def _axes(self) -> PassportRecordMeta:
        if self.verification_status in _FORBIDDEN_VERIFICATION:
            raise ValueError(
                "Passport verification_status must be unverified in 0052 "
                f"(got {self.verification_status.value})"
            )
        if self.verification_status != VerificationStatus.UNVERIFIED:
            raise ValueError("Passport verification_status must be unverified in 0052")
        if self.support_status not in _ALLOWED_SUPPORT:
            raise ValueError(
                "Passport support_status may only be not_provided or profile_supported "
                f"(got {self.support_status.value})"
            )
        if self.source_status == PassportSourceStatus.SUGGESTED_ACCEPTED:
            if self.support_status != SupportStatus.NOT_PROVIDED:
                raise ValueError(
                    "suggested_accepted must keep support_status=not_provided "
                    "(no evidence implication)"
                )
            if self.verification_status != VerificationStatus.UNVERIFIED:
                raise ValueError("suggested_accepted must remain unverified")
        if self.source_status in {
            PassportSourceStatus.UNKNOWN,
            PassportSourceStatus.NOT_PROVIDED,
        } and self.support_status == SupportStatus.PROFILE_SUPPORTED:
            raise ValueError(
                f"{self.source_status.value} source must not carry profile_supported"
            )
        return self


# ---------------------------------------------------------------------------
# Taxonomy reference
# ---------------------------------------------------------------------------


class PassportTaxonomyReference(PassportContractModel):
    """Advisory taxonomy reference — never replaces freeform user text."""

    kind: PassportTaxonomyKind
    input_text: str
    normalized_text: str | None = None
    taxonomy_id: str | None = None
    source: SourceType = SourceType.UNKNOWN
    confidence: ConfidenceLevel = ConfidenceLevel.UNKNOWN
    accepted_by_user: bool = False

    @field_validator("input_text")
    @classmethod
    def _input_text(cls, value: str) -> str:
        return _require_nonblank(value, "input_text")

    @field_validator("taxonomy_id")
    @classmethod
    def _taxonomy_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        return _validate_taxonomy_id(cleaned)

    @field_validator("normalized_text")
    @classmethod
    def _normalized_optional(cls, value: str | None) -> str | None:
        return _blank_to_none(value)

    @model_validator(mode="after")
    def _rules(self) -> PassportTaxonomyReference:
        if self.normalized_text is None:
            self.normalized_text = normalize_taxonomy_text(self.input_text)

        if self.taxonomy_id is None:
            if self.source != SourceType.UNKNOWN or self.confidence != ConfidenceLevel.UNKNOWN:
                raise ValueError(
                    "unknown taxonomy reference requires source=unknown and confidence=unknown"
                )
            if self.accepted_by_user:
                raise ValueError("accepted_by_user requires a taxonomy_id")
        else:
            if self.accepted_by_user is False and self.source == SourceType.UNKNOWN:
                # ID present with unknown source is allowed only if confidence unknown
                # and not accepted — still validate source/confidence pair
                pass
            if self.accepted_by_user and self.taxonomy_id is None:
                raise ValueError("accepted_by_user requires a taxonomy_id")

        validate_source_confidence(self.source, self.confidence)
        return self


# ---------------------------------------------------------------------------
# Section preferences
# ---------------------------------------------------------------------------


_DEFAULT_SECTION_ORDER: tuple[PassportSectionKey, ...] = (
    PassportSectionKey.PROFILE,
    PassportSectionKey.EXPERIENCE,
    PassportSectionKey.EDUCATION,
    PassportSectionKey.PROJECTS,
    PassportSectionKey.SKILLS,
    PassportSectionKey.CREDENTIALS,
    PassportSectionKey.TARGETS,
)


class PassportSectionPreference(PassportContractModel):
    section: PassportSectionKey
    order_index: int
    enabled: bool = True

    @field_validator("order_index")
    @classmethod
    def _order(cls, value: int) -> int:
        if value < 0:
            raise ValueError("order_index must be >= 0")
        return value


def default_section_preferences() -> list[PassportSectionPreference]:
    """Deterministic default section order for a new Passport."""
    return [
        PassportSectionPreference(section=key, order_index=index, enabled=True)
        for index, key in enumerate(_DEFAULT_SECTION_ORDER)
    ]


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------


class PassportProfile(PassportContractModel):
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
    bio_summary: str | None = Field(default=None, max_length=1000)
    declaration_text: str | None = None
    references_available_on_request: bool = False
    interests: list[str] = Field(default_factory=list)
    record_meta: PassportRecordMeta = Field(default_factory=PassportRecordMeta)

    @field_validator(
        "phone",
        "nationality",
        "linkedin_url",
        "github_url",
        "portfolio_url",
        "twitter_url",
        "address_city",
        "address_state",
        "address_country",
        "photo_url",
        "professional_headline",
        "bio_summary",
        "declaration_text",
        mode="before",
    )
    @classmethod
    def _optional_strings(cls, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            return _blank_to_none(value)
        return value

    @field_validator("other_social_links")
    @classmethod
    def _social_links(cls, values: list[Any]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for item in values or []:
            if not isinstance(item, dict):
                raise ValueError("other_social_links items must be dictionaries")
            out.append(item)
        return out

    @field_validator("interests")
    @classmethod
    def _interests(cls, values: list[str]) -> list[str]:
        return _normalize_string_list(values)


# ---------------------------------------------------------------------------
# Experience
# ---------------------------------------------------------------------------


class PassportExperience(PassportContractModel):
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
    record_meta: PassportRecordMeta = Field(default_factory=PassportRecordMeta)

    @field_validator("job_title")
    @classmethod
    def _job_title(cls, value: str) -> str:
        return _require_nonblank(value, "job_title")

    @field_validator("company_name")
    @classmethod
    def _company(cls, value: str) -> str:
        return _require_nonblank(value, "company_name")

    @field_validator("company_url", "location", "employment_type", mode="before")
    @classmethod
    def _optional(cls, value: Any) -> Any:
        if isinstance(value, str):
            return _blank_to_none(value)
        return value

    @field_validator("description_bullets")
    @classmethod
    def _bullets(cls, values: list[str]) -> list[str]:
        return _normalize_string_list(values)

    @field_validator("order_index")
    @classmethod
    def _order(cls, value: int) -> int:
        if value < 0:
            raise ValueError("order_index must be >= 0")
        return value

    @model_validator(mode="after")
    def _consistency(self) -> PassportExperience:
        _validate_date_order(self.start_date, self.end_date, is_current=self.is_current)
        _assert_taxonomy_kind(self.role_taxonomy, PassportTaxonomyKind.ROLE, "role_taxonomy")
        return self


# ---------------------------------------------------------------------------
# Education
# ---------------------------------------------------------------------------


class PassportEducation(PassportContractModel):
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
    record_meta: PassportRecordMeta = Field(default_factory=PassportRecordMeta)

    @field_validator("degree")
    @classmethod
    def _degree(cls, value: str) -> str:
        return _require_nonblank(value, "degree")

    @field_validator("institution")
    @classmethod
    def _institution(cls, value: str) -> str:
        return _require_nonblank(value, "institution")

    @field_validator("field_of_study", "location", "grade", mode="before")
    @classmethod
    def _optional(cls, value: Any) -> Any:
        if isinstance(value, str):
            return _blank_to_none(value)
        return value

    @field_validator("description_bullets", "relevant_coursework")
    @classmethod
    def _lists(cls, values: list[str]) -> list[str]:
        return _normalize_string_list(values)

    @field_validator("order_index")
    @classmethod
    def _order(cls, value: int) -> int:
        if value < 0:
            raise ValueError("order_index must be >= 0")
        return value

    @model_validator(mode="after")
    def _consistency(self) -> PassportEducation:
        _validate_date_order(self.start_date, self.end_date, is_current=self.is_current)
        return self


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------


class PassportProject(PassportContractModel):
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
    record_meta: PassportRecordMeta = Field(default_factory=PassportRecordMeta)

    @field_validator("title")
    @classmethod
    def _title(cls, value: str) -> str:
        return _require_nonblank(value, "title")

    @field_validator("description", "project_url", "role", mode="before")
    @classmethod
    def _optional(cls, value: Any) -> Any:
        if isinstance(value, str):
            return _blank_to_none(value)
        return value

    @field_validator("technologies", "key_achievements")
    @classmethod
    def _lists(cls, values: list[str]) -> list[str]:
        return _normalize_string_list(values)

    @field_validator("order_index")
    @classmethod
    def _order(cls, value: int) -> int:
        if value < 0:
            raise ValueError("order_index must be >= 0")
        return value

    @model_validator(mode="after")
    def _consistency(self) -> PassportProject:
        _validate_date_order(self.start_date, self.end_date, is_current=False)
        for ref in self.skill_taxonomy:
            if ref.kind != PassportTaxonomyKind.SKILL:
                raise ValueError("skill_taxonomy entries must have kind=skill")
        return self


# ---------------------------------------------------------------------------
# Skill
# ---------------------------------------------------------------------------


class PassportSkill(PassportContractModel):
    name: str
    skill_type: str = "technical"
    category: str | None = None
    proficiency: str | None = None
    order_index: int = 0
    taxonomy: PassportTaxonomyReference | None = None
    record_meta: PassportRecordMeta = Field(default_factory=PassportRecordMeta)

    @field_validator("name")
    @classmethod
    def _name(cls, value: str) -> str:
        return _require_nonblank(value, "name")

    @field_validator("skill_type")
    @classmethod
    def _skill_type(cls, value: str) -> str:
        return _require_nonblank(value, "skill_type")

    @field_validator("category", "proficiency", mode="before")
    @classmethod
    def _optional(cls, value: Any) -> Any:
        if isinstance(value, str):
            return _blank_to_none(value)
        return value

    @field_validator("order_index")
    @classmethod
    def _order(cls, value: int) -> int:
        if value < 0:
            raise ValueError("order_index must be >= 0")
        return value

    @model_validator(mode="after")
    def _taxonomy_kind(self) -> PassportSkill:
        _assert_taxonomy_kind(self.taxonomy, PassportTaxonomyKind.SKILL, "taxonomy")
        return self


# ---------------------------------------------------------------------------
# Credential reference
# ---------------------------------------------------------------------------


class PassportCredentialRef(PassportContractModel):
    """Thin credential/certification reference — not a verified credential."""

    credential_type: PassportCredentialType = PassportCredentialType.CERTIFICATION
    name: str
    issuing_organization: str
    issue_date: date | None = None
    expiry_date: date | None = None
    credential_id: str | None = None
    credential_url: str | None = None
    order_index: int = 0
    record_meta: PassportRecordMeta = Field(default_factory=PassportRecordMeta)

    @field_validator("name")
    @classmethod
    def _name(cls, value: str) -> str:
        return _require_nonblank(value, "name")

    @field_validator("issuing_organization")
    @classmethod
    def _issuer(cls, value: str) -> str:
        return _require_nonblank(value, "issuing_organization")

    @field_validator("credential_id", "credential_url", mode="before")
    @classmethod
    def _optional(cls, value: Any) -> Any:
        if isinstance(value, str):
            return _blank_to_none(value)
        return value

    @field_validator("order_index")
    @classmethod
    def _order(cls, value: int) -> int:
        if value < 0:
            raise ValueError("order_index must be >= 0")
        return value

    @model_validator(mode="after")
    def _dates(self) -> PassportCredentialRef:
        if (
            self.issue_date is not None
            and self.expiry_date is not None
            and self.expiry_date < self.issue_date
        ):
            raise ValueError("expiry_date must be on or after issue_date")
        return self


# ---------------------------------------------------------------------------
# Target
# ---------------------------------------------------------------------------


class PassportTarget(PassportContractModel):
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
    record_meta: PassportRecordMeta = Field(default_factory=PassportRecordMeta)

    @field_validator("target_role_text")
    @classmethod
    def _role_text(cls, value: str) -> str:
        return _require_nonblank(value, "target_role_text")

    @field_validator(
        "target_country",
        "target_region",
        "target_industry",
        "time_horizon",
        mode="before",
    )
    @classmethod
    def _optional(cls, value: Any) -> Any:
        if isinstance(value, str):
            return _blank_to_none(value)
        return value

    @field_validator("priority")
    @classmethod
    def _priority(cls, value: int) -> int:
        if value < 1 or value > 5:
            raise ValueError("priority must be between 1 and 5")
        return value

    @field_validator("order_index")
    @classmethod
    def _order(cls, value: int) -> int:
        if value < 0:
            raise ValueError("order_index must be >= 0")
        return value

    @model_validator(mode="after")
    def _taxonomy(self) -> PassportTarget:
        _assert_taxonomy_kind(self.role_taxonomy, PassportTaxonomyKind.ROLE, "role_taxonomy")
        return self


# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------


class CareerPassportContract(PassportContractModel):
    """Logical Passport aggregate. Persistence and HTTP schemas are later slices."""

    subject_id: UUID | None = None
    display_name: str | None = None
    headline: str | None = None
    summary: str | None = None
    visibility: PassportVisibility = PassportVisibility.PRIVATE
    version: int = 1

    section_preferences: list[PassportSectionPreference] = Field(
        default_factory=default_section_preferences
    )
    profile: PassportProfile = Field(default_factory=PassportProfile)
    experiences: list[PassportExperience] = Field(default_factory=list)
    education: list[PassportEducation] = Field(default_factory=list)
    projects: list[PassportProject] = Field(default_factory=list)
    skills: list[PassportSkill] = Field(default_factory=list)
    credentials: list[PassportCredentialRef] = Field(default_factory=list)
    targets: list[PassportTarget] = Field(default_factory=list)

    @field_validator("display_name", "headline", "summary", mode="before")
    @classmethod
    def _optional(cls, value: Any) -> Any:
        if isinstance(value, str):
            return _blank_to_none(value)
        return value

    @field_validator("version")
    @classmethod
    def _version(cls, value: int) -> int:
        if value < 1:
            raise ValueError("version must be >= 1")
        return value

    @model_validator(mode="after")
    def _section_prefs(self) -> CareerPassportContract:
        seen: set[PassportSectionKey] = set()
        for pref in self.section_preferences:
            if pref.section in seen:
                raise ValueError(f"duplicate section preference: {pref.section.value}")
            seen.add(pref.section)
        return self
