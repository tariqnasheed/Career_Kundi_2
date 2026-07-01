"""
db/models/audit.py
======================
Cross-cutting observability + compliance tables:

- `AuditLog`   — every agent action / tool invocation, per the Security
  Architecture mandate (§3.4 "Audit Logging"): timestamp, user, action,
  input/output HASHES (never raw PII), token count, latency.
- `TokenUsageRecord` — per-request token consumption, feeding the Usage
  Analytics Dashboard (§3.3) and the CostMonitorAgent's budget enforcement.
- `FeedbackRecord` — thumbs up/down on generated content (§2 "Feedback
  Loops"), used to re-rank retrieval and adjust prompts for future calls.
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import UUIDPrimaryKeyMixin


class AuditLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "audit_logs"

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    feature: Mapped[str] = mapped_column(String(50))       # job_search | cv_builder | roadmap | chatbot
    agent_name: Mapped[str] = mapped_column(String(100))     # e.g. "JobScraperAgent"
    action_type: Mapped[str] = mapped_column(String(50))      # tool_call | generation | reflection | rejection
    input_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)   # sha256, NOT raw input
    output_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class TokenUsageRecord(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "token_usage_records"

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    feature: Mapped[str] = mapped_column(String(50))
    model_used: Mapped[str] = mapped_column(String(50))  # gemini-2.5-flash | gemini-2.5-pro | mock
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_hit: Mapped[bool] = mapped_column(default=False)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)


class FeedbackRecord(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "feedback_records"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    feature: Mapped[str] = mapped_column(String(50))
    entity_type: Mapped[str] = mapped_column(String(50))  # interview_question | study_material | resource | cv_bullet
    entity_id: Mapped[str] = mapped_column(String(255))
    rating: Mapped[str] = mapped_column(String(10))  # up | down
    comment: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
