"""
db/models/memory.py
=======================
`AgentMemory` — the persistence layer behind "Agentic Memory" (§2 + every
feature's mandate to read/write user memory). Stores arbitrary structured
memory keyed by (user, namespace, key) so any agent team can read context
relevant to its feature without leaking another feature's private state.

Examples of rows:
  namespace="career_goals",     key="target_role",       value={"role": "Senior Data Engineer"}
  namespace="job_search",       key="recent_queries",     value={"queries": [...]}
  namespace="roadmap_progress", key="<roadmap_id>",       value={"completed_skills": [...]}
  namespace="chat_preferences", key="tone",               value={"preference": "concise"}
"""

import uuid

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AgentMemory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "agent_memory"
    __table_args__ = (UniqueConstraint("user_id", "namespace", "key", name="uq_agent_memory_scope"),)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    namespace: Mapped[str] = mapped_column(String(100))  # e.g. "career_goals", "job_search", "roadmap_progress"
    key: Mapped[str] = mapped_column(String(255))
    value: Mapped[dict] = mapped_column(JSON, default=dict)
