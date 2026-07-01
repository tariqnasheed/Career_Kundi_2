"""
db/models/assets.py
===================
GeneratedAsset — reusable AI-generated content library.

Assets are keyed by (user_id, category, asset_key) so the same query can
retrieve a cached explanation, question bank, or CV phrase without re-running
a full agent pipeline.

Categories:
  skill_explanation     Plain-language explanation of a technical skill
  interview_question    Q&A pair for a specific skill / role combination
  roadmap_milestone     Milestone description + activity list for a target role
  cv_phrase             Improved bullet alternative for a specific experience
  cover_letter_para     Cover letter paragraph reusable across applications
  badge_description     Badge flavour text (generated at badge award time)
  study_note            Study card / summary for a topic
"""

import uuid

from sqlalchemy import JSON, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class GeneratedAsset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "generated_assets"
    __table_args__ = (
        UniqueConstraint("user_id", "category", "asset_key", name="uq_asset_user_cat_key"),
        Index("ix_asset_user_category", "user_id", "category"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )

    # --- Classification -------------------------------------------------------
    category: Mapped[str] = mapped_column(String(60))
    # Stable lookup key, e.g. "python_oop_explanation", "react_senior_q42", "cv_bullet_we_001"
    asset_key: Mapped[str] = mapped_column(String(255))

    # --- Content -------------------------------------------------------------
    # Primary text payload (the main usable content — explanation, question text, phrase, etc.)
    content_text: Mapped[str] = mapped_column(Text, default="")
    # Structured extras (alternatives list, difficulty, tags, source citations, etc.)
    content_meta: Mapped[dict] = mapped_column(JSON, default=dict)

    # --- Context that produced this asset ------------------------------------
    # The pipeline that created it: "cv_builder", "roadmap", "interview_pack", etc.
    source_pipeline: Mapped[str | None] = mapped_column(String(60), nullable=True)
    # Model tier used: "flash" | "pro" | "gemini-pro-1.5" (for cache hygiene decisions)
    model_tier: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # Input fingerprint: SHA-256 of the parameters that produced this asset so
    # stale entries can be invalidated when the underlying profile/job changes.
    input_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    user: Mapped["User"] = relationship(back_populates="generated_assets")  # noqa: F821
