"""
schemas/cv_builder.py
=========================
Pydantic request/response contracts for the CV Builder feature (§4.3).

Two distinct concerns live here:

1. **API contracts** (`CVGenerateRequest`, `CVRead`, `BulletImprovementRequest`,
   `BulletImprovementResult`, `CVExportRequest`) — what the route layer in
   `app/api/routes/cv_builder.py` actually sends/receives over HTTP.
2. **The agent pipeline's output contract** (`CVGenerationResult` and its
   nested models) — the JSON schema handed to `get_llm().generate()` as
   `json_schema=` in live mode, and the exact shape `mock_data.py` must
   produce in mock mode, so both code paths are interchangeable from the
   Reflector's point of view.

As with `schemas/job_search.py`, list fields are deliberately unbounded —
the agent decides how many enhanced bullets / prioritized skills / ATS
keywords are genuinely supported by the input, never a schema-enforced cap.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.agents.cv_builder.studio_template import (
    STUDIO_META_SECTION_ID,
    extract_studio_template_id,
    validate_studio_template_id,
)


class _ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Advisory taxonomy meta (0051-F8; stored in section_config, no DB migration) -------

TAXONOMY_META_SECTION_ID = "_taxonomy"
CV_META_SECTION_IDS: frozenset[str] = frozenset({STUDIO_META_SECTION_ID, TAXONOMY_META_SECTION_ID})


class CVTaxonomyMeta(BaseModel):
    """
    Optional advisory Role Intelligence payload persisted as a reserved
    section_config row (`section_id="_taxonomy"`). Never required for CV
    create/save/export. Does not imply verified external taxonomy coverage.
    """

    target_role_text: str | None = None
    matched_role_id: str | None = None
    matched_skill_id: str | None = None
    normalized_text: str | None = None
    source: str | None = None
    confidence: str | None = None
    explanation: str | None = None
    accepted_by_user: bool = False
    kept_freeform: bool = False
    matched_role_title: str | None = None


def extract_taxonomy_meta(section_config: list[Any] | None) -> CVTaxonomyMeta | None:
    """Pull `_taxonomy` meta from section_config if present."""
    for item in section_config or []:
        if not isinstance(item, dict):
            continue
        if item.get("section_id") != TAXONOMY_META_SECTION_ID:
            continue
        payload = {k: v for k, v in item.items() if k not in ("section_id", "enabled")}
        return CVTaxonomyMeta.model_validate(payload)
    return None


def inject_taxonomy_meta(
    section_config: list[Any] | None,
    taxonomy: CVTaxonomyMeta | None,
) -> list[dict[str, Any]]:
    """
    Return a copy of section_config with the `_taxonomy` meta entry replaced
    (or removed when taxonomy is None). Preserves `_studio` and content rows.
    """
    cleaned: list[dict[str, Any]] = []
    for item in section_config or []:
        if isinstance(item, dict) and item.get("section_id") == TAXONOMY_META_SECTION_ID:
            continue
        if isinstance(item, dict):
            cleaned.append(dict(item))
    if taxonomy is None:
        return cleaned
    row: dict[str, Any] = {
        "section_id": TAXONOMY_META_SECTION_ID,
        "enabled": True,
        **taxonomy.model_dump(exclude_none=False),
    }
    cleaned.append(row)
    return cleaned


def content_section_config(section_config: list[Any] | None) -> list[dict[str, Any]]:
    """section_config without reserved `_studio` / `_taxonomy` meta rows."""
    out: list[dict[str, Any]] = []
    for item in section_config or []:
        if not isinstance(item, dict):
            continue
        sid = item.get("section_id")
        if sid in CV_META_SECTION_IDS:
            continue
        out.append(dict(item))
    return out


def filter_content_section_ids(section_ids: list[str] | None) -> list[str] | None:
    """Drop reserved meta ids if a client accidentally includes them."""
    if section_ids is None:
        return None
    return [sid for sid in section_ids if sid not in CV_META_SECTION_IDS]


# --- CV generation request/response ---------------------------------------------------


class SectionConfigItem(BaseModel):
    section_id: str
    enabled: bool = True


class ManualProfileInput(BaseModel):
    """
    Minimal intake for Quick CV generation. Never mutates Profile or Passport —
    it only informs a GeneratedCV snapshot for this request.
    """

    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    target_role: str = Field(..., min_length=1)
    career_level: Literal["beginner", "intermediate", "advanced", "expert"]
    summary_context: str | None = None
    skills_text: str | None = None
    experience_text: str | None = None
    education_text: str | None = None
    projects_text: str | None = None


class CVGenerateRequest(BaseModel):
    """
    `section_ids=None` means "include every section the profile actually has
    data for" (the CV Builder's default, no-thinking-required path);
    explicitly passing a list lets the user toggle sections off, per §4.3
    "Dynamic Section Toggles".

    `generation_mode="role_targeted"` generates full section content for a
    different target role via the model. Section toggles only control which
    sections appear — the model writes the content for each enabled section.

    `generation_mode="quick_intake"` builds a GeneratedCV from
    `manual_profile_input` (minimum name/role/level). It does not mutate
    Profile or Passport and must not invent employers, degrees, or certifications.

    `studio_template_id` is the CVB-F2 gallery id (15 templates). Persisted in
    section_config JSON meta — not the same as `template` (PDF style family).

    `taxonomy` is optional advisory Role Intelligence meta (0051-F8).
    """

    name: str | None = Field(default=None, description="Display name for this saved CV, e.g. 'Backend Eng — Acme'")
    target_job_id: uuid.UUID | None = Field(default=None, description="Tailor content toward this saved job, if any")
    template: Literal["modern", "classic", "compact", "creative"] = "modern"
    studio_template_id: str | None = Field(
        default=None,
        description="CVB-F2 gallery template id (e.g. bold-sidebar). Validated against the 15-template catalog.",
    )
    section_ids: list[str] | None = Field(default=None, description="None = every populated section")
    tone: Literal["concise", "detailed", "executive"] = "concise"
    generation_mode: Literal["profile", "role_targeted", "quick_intake"] = Field(
        default="profile",
        description=(
            "profile = enhance existing profile data; "
            "role_targeted = model generates sections for a different role; "
            "quick_intake = generate from manual_profile_input without mutating Profile/Passport"
        ),
    )
    target_role_title: str | None = Field(
        default=None,
        description="Required when generation_mode=role_targeted — the job role to generate the CV for",
    )
    target_role_description: str | None = Field(
        default=None,
        description="Optional role/JD context when generation_mode=role_targeted",
    )
    manual_profile_input: ManualProfileInput | None = Field(
        default=None,
        description="Required when generation_mode=quick_intake",
    )
    taxonomy: CVTaxonomyMeta | None = Field(
        default=None,
        description="Optional advisory taxonomy meta stored in section_config._taxonomy",
    )

    @field_validator("studio_template_id")
    @classmethod
    def _validate_studio_template_id(cls, value: str | None) -> str | None:
        return validate_studio_template_id(value)

    @model_validator(mode="after")
    def _validate_role_targeted(self) -> "CVGenerateRequest":
        if self.generation_mode == "role_targeted" and not (self.target_role_title or "").strip():
            raise ValueError("target_role_title is required when generation_mode is role_targeted.")
        if self.generation_mode == "quick_intake":
            if self.manual_profile_input is None:
                raise ValueError("manual_profile_input is required when generation_mode is quick_intake.")
            if not (self.manual_profile_input.target_role or "").strip():
                raise ValueError("manual_profile_input.target_role is required for quick_intake.")
        return self


class CVRegenerateRequest(CVGenerateRequest):
    """Same shape as a fresh generation — regenerating just re-runs the pipeline against an existing saved CV row."""


class CVUpdateRequest(BaseModel):
    """
    Lightweight save of draft metadata without re-running the AI pipeline.
    Used by Save Draft when a CV version already exists (CVB-F4).
    """

    name: str | None = Field(default=None, description="Display name for this saved CV")
    template: Literal["modern", "classic", "compact", "creative"] | None = Field(
        default=None,
        description="PDF/backend style family stored on the CV row",
    )
    studio_template_id: str | None = Field(
        default=None,
        description="CVB-F2 gallery template id to persist in section_config meta",
    )
    section_ids: list[str] | None = Field(
        default=None,
        description="When set, replaces enabled section toggles (studio + taxonomy meta preserved/merged)",
    )
    taxonomy: CVTaxonomyMeta | None = Field(
        default=None,
        description="When set, replaces section_config._taxonomy; when omitted, existing taxonomy meta is preserved",
    )

    @field_validator("studio_template_id")
    @classmethod
    def _validate_studio_template_id(cls, value: str | None) -> str | None:
        return validate_studio_template_id(value)


class CVRead(_ORMModel):
    id: uuid.UUID
    user_id: uuid.UUID
    target_job_id: uuid.UUID | None = None
    name: str
    template: str
    section_config: list[dict] = Field(default_factory=list)
    rendered_content: dict = Field(default_factory=dict)
    export_format_last_used: str | None = None
    created_at: datetime
    updated_at: datetime
    studio_template_id: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _hydrate_studio_template_id(cls, data: Any) -> Any:
        """Derive studio_template_id from section_config meta for ORM and dict inputs."""
        if hasattr(data, "section_config"):
            cfg = getattr(data, "section_config", None) or []
            studio = extract_studio_template_id(cfg)
            return {
                "id": data.id,
                "user_id": data.user_id,
                "target_job_id": data.target_job_id,
                "name": data.name,
                "template": data.template,
                "section_config": cfg,
                "rendered_content": data.rendered_content or {},
                "export_format_last_used": data.export_format_last_used,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
                "studio_template_id": studio,
            }
        if isinstance(data, dict) and data.get("studio_template_id") is None:
            studio = extract_studio_template_id(data.get("section_config") or [])
            return {**data, "studio_template_id": studio}
        return data


class CVExportRequest(BaseModel):
    format: Literal["pdf", "docx", "markdown"] = "pdf"


# --- Bullet improvement ("Improve with AI" on a single bullet) -------------------------


class BulletImprovementRequest(BaseModel):
    bullet_text: str
    context_role_title: str | None = Field(default=None, description="e.g. the WorkExperience.job_title it belongs to")
    context_company_name: str | None = None
    section_type: Literal["work_experience", "project", "education", "volunteer", "custom"] = "work_experience"
    target_job_id: uuid.UUID | None = Field(default=None, description="Optional JD to align the rewrite toward")

    @model_validator(mode="after")
    def _require_text(self) -> "BulletImprovementRequest":
        if not self.bullet_text or not self.bullet_text.strip():
            raise ValueError("bullet_text must not be empty.")
        return self


class BulletImprovementResult(BaseModel):
    original_bullet: str
    improved_bullet: str
    rationale: str
    citations: list[dict] = Field(default_factory=list)
    confidence_score: float = 0.0


# --- Agent pipeline output contract (used as the LLM json_schema AND the mock_data shape) --


class EnhancedBullet(BaseModel):
    original: str
    enhanced: str
    rationale: str


class EnhancedEntryBullets(BaseModel):
    """Enhanced bullets for one WorkExperience / Project / Volunteer / CustomSectionEntry, keyed by its real ORM id."""

    entry_id: str
    enhanced_bullets: list[EnhancedBullet] = Field(default_factory=list)


class CVGenerationResult(BaseModel):
    professional_summary: str = ""
    summary_rationale: str = ""
    enhanced_work_experiences: list[EnhancedEntryBullets] = Field(default_factory=list)
    enhanced_projects: list[EnhancedEntryBullets] = Field(default_factory=list)
    prioritized_skills: list[str] = Field(default_factory=list)
    ats_keywords_matched: list[str] = Field(default_factory=list)
    sections_included: list[str] = Field(default_factory=list)
    citations: list[dict] = Field(default_factory=list)
    confidence_score: float = 0.0
    needs_manual_input: bool = False
    manual_input_reason: str | None = None
    generation_mode: Literal["profile", "role_targeted"] = "profile"
    generated_sections: dict[str, Any] = Field(
        default_factory=dict,
        description="Role-targeted mode: full section payloads keyed by section_id (summary, experience, skills, …)",
    )
