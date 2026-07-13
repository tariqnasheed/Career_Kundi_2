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


class CompanyResearchSourceRead(BaseModel):
    """One captured company research source (Iteration 004E-C)."""

    url: str
    source_type: str
    title: str | None = None
    extracted_facts: list[str] = Field(default_factory=list)
    confidence: str = "medium"


class CompanyResearchRead(BaseModel):
    """Company profile and source-cited research metadata (Iteration 004E-C)."""

    company_name: str | None = None
    company_domain: str | None = None
    official_website: str | None = None
    company_overview: str | None = None
    products_services: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    markets: list[str] = Field(default_factory=list)
    mission_or_values: list[str] = Field(default_factory=list)
    company_size: str | None = None
    headquarters: str | None = None
    source_urls: list[str] = Field(default_factory=list)
    sources: list[CompanyResearchSourceRead] = Field(default_factory=list)
    research_confidence: str = "unavailable"
    source_status: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    research_methods: list[str] = Field(default_factory=list)


class JobPostingExtractionRead(BaseModel):
    """Metadata from job posting URL extraction (Iteration 004E-B)."""

    source_url: str
    final_url: str | None = None
    title: str | None = None
    company_name: str | None = None
    company_profile: str | None = None
    description: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    preferred_qualifications: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    location: str | None = None
    seniority: str | None = None
    employment_type: str | None = None
    date_posted: str | None = None
    valid_through: str | None = None
    salary_text: str | None = None
    extraction_confidence: str = "failed"
    extraction_methods: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    source_status: dict[str, str] = Field(default_factory=dict)


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
    job_posting_url: str | None = Field(
        default=None,
        description="Optional job posting URL override for link extraction before generation.",
    )
    extract_from_url: bool = Field(
        default=True,
        description="When true and a posting URL is present, extract fields before generating the pack.",
    )
    company_url: str | None = Field(
        default=None,
        description="Optional company profile page URL override for company research before generation.",
    )
    research_company: bool = Field(
        default=True,
        description="When true and a company URL is present, extract company context before generating the pack.",
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
    # 004E-E finalized per-question module metadata (additive)
    question_id: str | None = None
    question_text: str | None = None
    answer_summary: str | None = None
    source_items_used: list[str] = Field(default_factory=list)
    source_types_used: list[str] = Field(default_factory=list)
    source_priority_used: list[str] = Field(default_factory=list)
    core_idea: str | None = None
    what_this_question_tests: str | None = None
    technical_or_workflow_skills_covered: list[str] = Field(default_factory=list)
    key_definitions: list[dict[str, str]] = Field(default_factory=list)
    key_principles: list[str] = Field(default_factory=list)
    step_by_step_method: list[str] = Field(default_factory=list)
    beginner_explanation: str | None = None
    intermediate_explanation: str | None = None
    advanced_explanation: str | None = None
    interview_application: str | None = None
    likely_follow_ups: list[str] = Field(default_factory=list)
    saved_material_insight: str | None = None
    document_library_insight: str | None = None
    model_insight: str | None = None
    web_or_company_source_insight: str | None = None
    source_status: dict[str, str] = Field(default_factory=dict)
    fallback_status: str | None = None


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


class JobIntelligenceItemRead(BaseModel):
    item_type: str
    text: str
    source: str
    importance: str
    covered: bool = False
    related_question_ids: list[str] = Field(default_factory=list)
    missing_reason: str | None = None
    item_id: str | None = None
    source_label: str | None = None
    item_text: str | None = None
    source_type: str | None = None
    action: str | None = None


class CoverageAuditItemRead(BaseModel):
    item_id: str | None = None
    item_type: str
    item_text: str
    source_type: str
    source_label: str = ""
    covered: bool = False
    related_question_ids: list[str] = Field(default_factory=list)
    missing_reason: str | None = None
    action: str = "pending"


class SourceLadderStatusRead(BaseModel):
    user_fields: str = "thin"
    link_extraction: str = "not_present"
    company_research: str = "not_present"
    model_knowledge: str = "disabled"
    document_library: str = "not_configured"
    local_fallback: str = "used"
    web_research: str | None = None


class JobIntelligenceProfileRead(BaseModel):
    job_title: str
    company_name: str | None = None
    completeness_score: int = 0
    warnings: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    daily_responsibilities: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    tools_software: list[str] = Field(default_factory=list)
    compliance_safety_ethics: list[str] = Field(default_factory=list)
    seniority_level: str | None = None
    source_status: dict[str, str] = Field(default_factory=dict)
    source_ladder: SourceLadderStatusRead | None = None
    summary: str = ""


class CoverageAuditRead(BaseModel):
    total_items: int = 0
    covered_items: int = 0
    coverage_score: int = 0
    warnings: list[str] = Field(default_factory=list)
    added_question_count: int = 0
    responsibilities_covered: int = 0
    skills_covered: int = 0
    tools_covered: int = 0
    company_context_covered: bool = False
    compliance_covered: bool = False
    has_difficulty_progression: bool = False
    has_practical_or_scenario: bool = False
    audit_items: list[CoverageAuditItemRead] = Field(default_factory=list)
    missing_items: list[CoverageAuditItemRead] = Field(default_factory=list)


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
    question_source_items: list[str] = Field(default_factory=list)
    question_source_types: list[str] = Field(default_factory=list)
    source_priority_used: list[str] = Field(default_factory=list)
    coverage_item_ids: list[str] = Field(default_factory=list)
    practice_tasks: list[str] = Field(default_factory=list)
    revision_notes: list[str] = Field(default_factory=list)
    citations: list[dict] = Field(default_factory=list)
    skill_tag: str | None = None
    estimated_answer_time_minutes: int = 5
    # Provenance of the authored prose (model_answer / common_mistakes / study).
    # "gemini" = fully LLM-authored & preserved; "gemini_partial" = some fields
    # LLM-authored, others filled deterministically; "deterministic_fallback" =
    # live mode but the LLM produced nothing usable so templates were used;
    # "deterministic_mock" = offline/mock mode. Lets us verify a pack was truly
    # dynamic rather than silently falling back to the family template engine.
    content_source: Literal[
        "gemini",
        "gemini_partial",
        "deterministic_fallback",
        "deterministic_mock",
    ] | None = None


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
    job_intelligence: JobIntelligenceProfileRead | None = None
    coverage_audit: CoverageAuditRead | None = None
    job_posting_extraction: JobPostingExtractionRead | None = None
    company_research: CompanyResearchRead | None = None


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
