"""
db/models/cv.py
===================
`GeneratedCV` — a saved, generated CV build. Stores the configuration
(template, toggled sections, order) needed to regenerate or re-export the
CV, plus a snapshot of the rendered content so past versions remain
viewable even if the underlying Profile changes later.
"""

import uuid

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class GeneratedCV(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "generated_cvs"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    target_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("saved_jobs.id", ondelete="SET NULL"), nullable=True
    )

    name: Mapped[str] = mapped_column(String(255), default="Untitled CV")
    template: Mapped[str] = mapped_column(String(50), default="modern")

    # Ordered list of {"section_id": str, "enabled": bool} — drives both the
    # toggle panel state and the render order in the live preview / export.
    section_config: Mapped[list] = mapped_column(JSON, default=list)

    # Snapshot of the fully rendered CV content at generation time (so the
    # CV remains viewable/exportable even if the profile changes later).
    rendered_content: Mapped[dict] = mapped_column(JSON, default=dict)

    export_format_last_used: Mapped[str | None] = mapped_column(String(10), nullable=True)  # pdf|docx|markdown

    user: Mapped["User"] = relationship(back_populates="cvs")  # noqa: F821
