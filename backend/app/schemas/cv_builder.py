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

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- CV generation request/response ---------------------------------------------------


class SectionConfigItem(BaseModel):
    section_id: str
    enabled: bool = True


class CVGenerateRequest(BaseModel):
    """
    `section_ids=None` means "include every section the profile actually has
    data for" (the CV Builder's default, no-thinking-required path);
    explicitly passing a list lets the user toggle sections off, per §4.3
    "Dynamic Section Toggles".

    `generation_mode="role_targeted"` generates full section content for a
    different target role via the model. Section toggles only control which
    sections appear — the model writes the content for each enabled section.
    """

    name: str | None = Field(default=None, description="Display name for this saved CV, e.g. 'Backend Eng — Acme'")
    target_job_id: uuid.UUID | None = Field(default=None, description="Tailor content toward this saved job, if any")
    template: Literal["modern", "classic", "compact", "creative"] = "modern"
    section_ids: list[str] | None = Field(default=None, description="None = every populated section")
    tone: Literal["concise", "detailed", "executive"] = "concise"
    generation_mode: Literal["profile", "role_targeted"] = Field(
        default="profile",
        description="profile = enhance existing profile data; role_targeted = model generates all enabled sections for a different role",
    )
    target_role_title: str | None = Field(
        default=None,
        description="Required when generation_mode=role_targeted — the job role to generate the CV for",
    )
    target_role_description: str | None = Field(
        default=None,
        description="Optional role/JD context when generation_mode=role_targeted",
    )

    @model_validator(mode="after")
    def _validate_role_targeted(self) -> "CVGenerateRequest":
        if self.generation_mode == "role_targeted" and not (self.target_role_title or "").strip():
            raise ValueError("target_role_title is required when generation_mode is role_targeted.")
        return self


class CVRegenerateRequest(CVGenerateRequest):
    """Same shape as a fresh generation — regenerating just re-runs the pipeline against an existing saved CV row."""


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
