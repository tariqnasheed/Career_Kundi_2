"""
schemas/job_search.py
=========================
Pydantic request/response contracts for the Job Search & Discovery and
Interview Pack Generation endpoints (§4.1, §4.2).

Note the deliberate ABSENCE of any `max_length`/`max_items` constraint on
list fields like `requirements`, `extracted_skills`, or interview
questions — per §5's "no artificial limits" mandate, the agent pipeline
(not the schema layer) decides how many items are genuinely relevant, and
the schema must not silently truncate whatever it produces.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class _ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Job parsing / enrichment --------------------------------------------------------


class JobParseRequest(BaseModel):
    """
    Either `url` (direct paste of a job posting link, scraped via
    `app.tools.scraper`) or `pasted_text` (the user copies the job
    description directly) must be provided — never both empty, per §4.1
    "Job Search & Discovery — direct URL paste".
    """

    url: str | None = Field(default=None, description="Direct URL to a job posting")
    pasted_text: str | None = Field(default=None, description="Raw pasted job description text")

    @model_validator(mode="after")
    def _require_one_source(self) -> "JobParseRequest":
        if not (self.url or self.pasted_text):
            raise ValueError("Provide either 'url' or 'pasted_text'.")
        return self


class ExtractedSkill(BaseModel):
    skill: str
    category: Literal["technical", "soft", "tool", "domain"] = "technical"
    importance: Literal["critical", "high", "medium", "nice-to-have"] = "medium"


class VerificationSource(BaseModel):
    url: str
    matched_fields: list[str] = Field(default_factory=list)
    verified: bool = False


class SavedJobRead(_ORMModel):
    id: uuid.UUID
    source_url: str | None = None
    source_site: str | None = None
    import_method: str
    status: Literal["saved", "applied", "interviewing", "offered", "rejected"] = "saved"
    title: str
    company_name: str | None = None
    company_url: str | None = None
    location: str | None = None
    employment_type: str | None = None
    is_remote: bool | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    description_raw: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)
    extracted_skills: list[dict] = Field(default_factory=list)
    company_profile: dict = Field(default_factory=dict)
    verification_status: Literal["verified", "partial", "unverified"] = "unverified"
    verification_sources: list[dict] = Field(default_factory=list)
    match_score: float | None = None
    interview_pack_confidence: float | None = None
    interview_pack_generated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class JobStatusUpdate(BaseModel):
    """Body for `PATCH /job-search/{job_id}/status` — the application tracker."""

    status: Literal["saved", "applied", "interviewing", "offered", "rejected"]


class SavedJobCreate(BaseModel):
    """
    Payload for persisting a job the user has ALREADY reviewed on the client
    (the "Save Job" button on the Job Search page, after a URL-extraction
    preview and any manual edits) via `POST /job-search/`.

    Unlike `JobParseRequest`, this does not trigger the extraction pipeline —
    it carries the finished job fields directly. Every field is optional
    except `title`, and unknown extra fields are ignored so the client can
    post a slightly richer object without breaking this contract.
    """

    model_config = ConfigDict(extra="ignore")

    title: str = "Untitled Role"
    source_url: str | None = None
    source_site: str | None = None
    import_method: str = "manual"
    company_name: str | None = None
    company_url: str | None = None
    location: str | None = None
    employment_type: str | None = None
    is_remote: bool | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    description_raw: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)
    extracted_skills: list[dict] = Field(default_factory=list)
    company_profile: dict = Field(default_factory=dict)
    verification_status: Literal["verified", "partial", "unverified"] = "unverified"
    verification_sources: list[dict] = Field(default_factory=list)

    @field_validator(
        "source_url", "source_site", "company_name", "company_url", "location",
        "employment_type", "salary_min", "salary_max", "salary_currency", "description_raw",
        mode="before",
    )
    @classmethod
    def _blank_to_none(cls, v: object) -> object:
        # The frontend form sends "" (empty string) for untouched optional
        # fields — including the numeric salary inputs. Treat blank strings as
        # "unset" so float coercion doesn't fail and we don't persist empties.
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class JobEnrichmentResult(BaseModel):
    """What the agent pipeline returns; the route layer maps this onto a `SavedJob` row."""

    title: str
    company_name: str | None = None
    company_url: str | None = None
    location: str | None = None
    employment_type: str | None = None
    is_remote: bool | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)
    extracted_skills: list[ExtractedSkill] = Field(default_factory=list)
    company_profile: dict = Field(default_factory=dict)
    confidence_score: float = 0.0
    verification_status: Literal["verified", "partial", "unverified"] = "unverified"
    verification_sources: list[VerificationSource] = Field(default_factory=list)
    citations: list[dict] = Field(default_factory=list)
    needs_manual_input: bool = False
    manual_input_reason: str | None = None


# --- Interview Pack -----------------------------------------------------------------------


class InterviewPackRequest(BaseModel):
    """
    Optional steering for pack generation. `focus_areas` lets the user bias
    toward specific skills/topics; leaving it empty means the agent decides
    coverage purely from the job's own extracted skills/requirements.
    Deliberately no `num_questions` cap field — count is never user- or
    schema-bounded, per §4.2 "NO upper limit on question count".
    """

    focus_areas: list[str] = Field(default_factory=list)
    difficulty: Literal["entry", "mid", "senior", "auto"] = "auto"


class InterviewQuestion(BaseModel):
    category: Literal["behavioral", "technical", "system_design", "role_specific", "company_specific"]
    question: str
    why_asked: str
    ideal_answer_points: list[str] = Field(default_factory=list)
    follow_ups: list[str] = Field(default_factory=list)
    citations: list[dict] = Field(default_factory=list)
    skill_tag: str | None = None


class InterviewPackResult(BaseModel):
    questions: list[InterviewQuestion] = Field(default_factory=list)
    confidence_score: float = 0.0
    generated_at: datetime
    coverage_summary: dict[str, int] = Field(default_factory=dict)  # category -> count, for the UI's coverage chart


class InterviewPackRead(BaseModel):
    job_id: str
    questions: list[InterviewQuestion] = Field(default_factory=list)
    confidence_score: float | None = None
    generated_at: datetime | None = None
