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


class JobDiscoverRequest(BaseModel):
    """Natural-language + filter search against live job postings on the web."""

    q: str | None = Field(default=None, description="Role, skills, or natural-language query")
    location: str | None = None
    employment_type: str | None = None
    remote: bool | None = None
    salary_min: float | None = None
    experience_level: str | None = None
    date_posted: str | None = None
    url: str | None = Field(default=None, description="Direct job posting URL (paste field)")


class JobDiscoveryResult(BaseModel):
    """A single hit from web job discovery — not yet saved to the user's account."""

    title: str
    company_name: str | None = None
    location: str | None = None
    employment_type: str | None = None
    is_remote: bool | None = None
    snippet: str = ""
    source_url: str
    source_site: str | None = None
    salary_hint: str | None = None
    verified: bool = False


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
    has_interview_pack: bool = False
    created_at: datetime
    updated_at: datetime


class JobStatusUpdate(BaseModel):
    """Body for `PATCH /job-search/{job_id}/status` — the application tracker."""

    status: Literal["saved", "applied", "interviewing", "offered", "rejected"]


class SavedJobUpdate(BaseModel):
    """Body for `PATCH /job-search/{job_id}` — update reviewed job fields from the unified job form."""

    model_config = ConfigDict(extra="ignore")

    title: str | None = None
    source_url: str | None = None
    source_site: str | None = None
    company_name: str | None = None
    company_url: str | None = None
    location: str | None = None
    employment_type: str | None = None
    is_remote: bool | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    description_raw: str | None = None
    responsibilities: list[str] | None = None
    requirements: list[str] | None = None
    benefits: list[str] | None = None
    extracted_skills: list[dict] | None = None

    @field_validator(
        "source_url", "source_site", "company_name", "company_url", "location",
        "employment_type", "salary_min", "salary_max", "salary_currency", "description_raw",
        mode="before",
    )
    @classmethod
    def _blank_to_none(cls, v: object) -> object:
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


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
    include_study_material: bool = Field(
        default=True,
        description="When true, each question includes beginner-friendly study material (definitions, principles, explanations).",
    )


class InterviewStudyMaterial(BaseModel):
    """
    Zero-prior-knowledge study module for ONE interview question.
    Each section teaches every skill/concept mentioned in that question's answer.
    """

    overview: str = ""
    what_you_need_to_know_first: list[str] = Field(default_factory=list)
    definitions: list[dict[str, str]] = Field(
        default_factory=list,
        description='Glossary entries, e.g. [{"term": "REST", "definition": "..."}]',
    )
    skill_explanations: list[dict[str, str]] = Field(
        default_factory=list,
        description='Per-skill teaching, e.g. [{"skill": "Python", "explanation": "..."}]',
    )
    principles: list[str] = Field(default_factory=list)
    key_concepts: list[str] = Field(default_factory=list)
    step_by_step_breakdown: list[str] = Field(default_factory=list)
    explanations: list[str] = Field(default_factory=list)
    practical_example: str = ""
    common_mistakes: list[str] = Field(default_factory=list)
    how_to_answer_better: list[str] = Field(default_factory=list)
    practice_exercises: list[str] = Field(default_factory=list)
    revision_notes: list[str] = Field(default_factory=list)
    related_concepts: list[str] = Field(default_factory=list)
    estimated_reading_time_minutes: int | None = None


class StudySourceEntry(BaseModel):
    """One step in the study-material source ladder."""

    source_type: Literal["web", "model", "document_library", "local_fallback"]
    label: str = ""
    status: Literal["used", "available_not_used", "failed", "not_configured"] = "not_configured"
    url: str | None = None
    document_path: str | None = None
    confidence: float | None = None
    note: str = ""


class StudySourcesMetadata(BaseModel):
    """Source/fallback metadata attached to each question's study module."""

    used_source_types: list[str] = Field(default_factory=list)
    sources: list[StudySourceEntry] = Field(default_factory=list)
    summary: str = ""


class RoleOverview(BaseModel):
    role_name: str = ""
    summary: str = ""
    responsibilities: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    what_employers_expect: list[str] = Field(default_factory=list)
    skill_clusters: list[str] = Field(default_factory=list)


class InterviewQuestion(BaseModel):
    question_id: str | None = None
    category: Literal[
        "behavioral",
        "technical",
        "system_design",
        "role_specific",
        "company_specific",
        "hr",
        "daily_routine",
    ]
    question: str
    why_asked: str
    difficulty: Literal["Easy", "Medium", "Hard", "Expert"] = "Medium"
    related_skills: list[str] = Field(default_factory=list)
    model_answer: str = ""
    answer_explanation: str = ""
    ideal_answer_points: list[str] = Field(default_factory=list)
    evaluation_criteria: list[str] = Field(default_factory=list)
    common_mistakes: list[str] = Field(default_factory=list)
    follow_ups: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    study_material: InterviewStudyMaterial = Field(default_factory=InterviewStudyMaterial)
    study_sources: StudySourcesMetadata | None = None
    practice_tasks: list[str] = Field(default_factory=list)
    revision_notes: list[str] = Field(default_factory=list)
    citations: list[dict] = Field(default_factory=list)
    skill_tag: str | None = None
    estimated_answer_time_minutes: int = 5


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
    role_slug: str | None = None
    role_overview: RoleOverview | None = None
    library_status: Literal["generated", "library_reused", "library_fallback", "none"] = "generated"
    saved_documents: list[str] = Field(default_factory=list)
    fallback_message: str | None = None
    from_library: bool = False


class RolePackLibraryEntry(BaseModel):
    role_slug: str
    role_name: str
    category: str
    question_count: int = 0
    pdf_files: list[str] = Field(default_factory=list)
    last_updated: str | None = None
    folder: str | None = None


class RolePackLookupResponse(BaseModel):
    status: Literal["exact_match", "related_only", "none", "found"]
    message: str
    pack: InterviewPackRead | None = None
    related: list[RolePackLibraryEntry] = Field(default_factory=list)
