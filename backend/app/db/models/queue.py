"""
db/models/queue.py
==================
GenerationJob — background task record for heavy async generation work.

Job types (job_type):
  interview_pack_pdf   Full interview pack as downloadable PDF
  roadmap_pdf          Career roadmap export PDF
  cv_export            Multi-template CV bundle (PDF + DOCX)
  study_bundle         Complete practice material set
  practice_bank        Large interview question bank for a target role

Status flow:  pending → running → done | failed
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class GenerationJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "generation_jobs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )

    # --- Job identity --------------------------------------------------------
    job_type: Mapped[str] = mapped_column(String(60))
    # Human-readable label shown in the UI queue panel
    label: Mapped[str] = mapped_column(String(255), default="")

    # --- Status --------------------------------------------------------------
    # pending | running | done | failed | cancelled
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)   # 0-100
    # Current step description for granular progress display
    current_step: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # --- Input / output ------------------------------------------------------
    # Serialised agent input parameters (job_id, cv_id, roadmap_id, etc.)
    input_params: Mapped[dict] = mapped_column(JSON, default=dict)
    # Serialised result: {"download_url": str, "file_size": int, "pages": int, ...}
    result_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Timing --------------------------------------------------------------
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="generation_jobs")  # noqa: F821
