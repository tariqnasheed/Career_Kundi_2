"""
db/models/chat.py
=====================
Conversation persistence for the AI Assistant Chatbot (§4.7). A
`ChatSession` groups a sequence of `ChatMessage`s so the MemoryAgent can
load recent history as context for follow-up questions within and across
browser sessions.
"""

import uuid

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ChatSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "chat_sessions"
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255), default="New conversation")

    user: Mapped["User"] = relationship(back_populates="chat_sessions")  # noqa: F821
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at"
    )


class ChatMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "chat_messages"
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(20))  # user | assistant | system
    content: Mapped[str] = mapped_column(Text)

    # Inline citations: list[{"n": int, "title": str, "url": str}]
    citations: Mapped[list] = mapped_column(JSON, default=list)
    # IntentClassifierAgent's routing decision + any ActionDispatchAgent result,
    # kept for debugging/audit and for the "Re-do" button in the Dashboard feed.
    intent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    action_result: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence_score: Mapped[float | None] = mapped_column(nullable=True)

    session: Mapped["ChatSession"] = relationship(back_populates="messages")
