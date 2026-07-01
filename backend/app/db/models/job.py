"""
db/models/job.py
====================
`SavedJob` — a job posting the user has saved, either from the Smart Search
results or from a directly pasted URL (§4.1). Stores both the raw scraped
payload and the structured, agent-enriched fields so the Interview Pack and
CV Builder features can reuse it without re-scraping.
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class SavedJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "saved_jobs"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))

    # --- Source ---------------------------------------------------------------
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    source_site: Mapped[str | None] = mapped_column(String(100), nullable=True)  # LinkedIn, Indeed, pasted-url, manual
    import_method: Mapped[str] = mapped_column(String(20), default="search")  # search | pasted_url | manual

    # Application-tracking status the user manages from the saved-jobs list /
    # tracker board: saved (default) -> applied -> interviewing -> offered -> rejected.
    # `server_default` ensures existing rows get a value when this column is added.
    status: Mapped[str] = mapped_column(String(20), default="saved", server_default="saved")

    # --- Structured job fields (populated by JobScraperAgent / JobEnricherAgent) ---
    title: Mapped[str] = mapped_column(String(255))
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    employment_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_remote: Mapped[bool | None] = mapped_column(nullable=True)
    salary_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    date_posted: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    description_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsibilities: Mapped[list] = mapped_column(JSON, default=list)  # list[str]
    requirements: Mapped[list] = mapped_column(JSON, default=list)      # list[str]
    benefits: Mapped[list] = mapped_column(JSON, default=list)          # list[str]

    # GraphRAG/RAG enrichment output: extracted skill clusters with metadata,
    # e.g. [{"skill": "Distributed Systems", "category": "technical", "importance": "high"}, ...]
    extracted_skills: Mapped[list] = mapped_column(JSON, default=list)
    company_profile: Mapped[dict] = mapped_column(JSON, default=dict)

    # Cross-source verification result (CrossVerifierAgent) — §4.1 "Cross-Source Verification"
    verification_status: Mapped[str] = mapped_column(String(20), default="unverified")  # verified|partial|unverified
    verification_sources: Mapped[list] = mapped_column(JSON, default=list)  # list[{"url", "matched_fields"}]

    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # fit vs. user's profile, 0-100

    # Interview Pack (§4.2) — generated on demand against this job's enriched
    # fields. Stored as a JSON list with NO fixed-length schema constraint so
    # the "no artificial limits on question count" mandate is representable
    # at the persistence layer too, not just in the agent prompt.
    interview_pack: Mapped[list] = mapped_column(JSON, default=list)
    interview_pack_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    interview_pack_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="saved_jobs")  # noqa: F821
    applications: Mapped[list["JobApplication"]] = relationship(  # noqa: F821
        back_populates="job", cascade="all, delete-orphan"
    )
