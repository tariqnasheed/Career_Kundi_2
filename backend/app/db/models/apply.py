"""
db/models/apply.py
==================
JobApplication — tracks every auto-apply attempt and manual application log.

Safety contract (enforced at agent + route level, documented at model level):
  - user_confirmed MUST be True before any submission is attempted
  - password_used is NEVER stored (column intentionally absent)
  - submitted_data stores only what was sent (CV metadata + public profile fields)

Status flow:
  draft → awaiting_confirmation → submitting → submitted | failed | blocked | manual_required
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, JSON, String, Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class JobApplication(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "job_applications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("saved_jobs.id", ondelete="CASCADE")
    )
    # The CV used for this application (NULL = used profile data directly)
    cv_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("generated_cvs.id", ondelete="SET NULL"), nullable=True
    )

    # --- Safety gate ---------------------------------------------------------
    # The user must explicitly confirm before we proceed. Never True unless
    # the user pressed "Confirm & Submit" in the UI.
    user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # --- Status --------------------------------------------------------------
    # draft | awaiting_confirmation | submitting | submitted | failed | blocked | manual_required
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)
    # Human-readable status detail (shown directly in the UI)
    status_detail: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # --- Cover letter --------------------------------------------------------
    cover_letter_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    cover_letter_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Submission record ---------------------------------------------------
    # What was actually sent (CV metadata, public profile fields used, form fields filled)
    submitted_data: Mapped[dict] = mapped_column(JSON, default=dict)
    # Platform-side confirmation (e.g. application ID from the job board)
    platform_confirmation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # --- Failure / fallback --------------------------------------------------
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    # URL for manual fallback when automation was blocked
    manual_apply_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    # Structured progress log: list[{"step": str, "status": str, "ts": iso-str, "detail": str}]
    tracker_log: Mapped[list] = mapped_column(JSON, default=list)

    user: Mapped["User"] = relationship(back_populates="job_applications")       # noqa: F821
    job:  Mapped["SavedJob"] = relationship(back_populates="applications")        # noqa: F821
