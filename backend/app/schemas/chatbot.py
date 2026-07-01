"""
schemas/chatbot.py
======================
Pydantic request/response contracts for the AI Assistant Chatbot (§4.7).

Field names on ``*Read`` models are kept in exact lockstep with
``app/db/models/chat.py`` (``ChatSession`` / ``ChatMessage``) and
``app/db/models/memory.py`` (``AgentMemory``) so ``model_validate(orm_row)``
round-trips cleanly.

One intentionally transient field: ``ChatMessageRead.suggested_followups``
has no ORM column (follow-up suggestions are ephemeral — only populated
in the response to the ``POST .../messages`` endpoint that generated them;
re-fetching the message later returns an empty list rather than stale
suggestions that may no longer make sense).  This mirrors the pattern used
by ``schemas/roadmap.py``'s ``generation_confidence`` / ``generation_citations``
fields, which are also set only at generation time.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class _ORMModel(BaseModel):
    """Base for all read-schemas that map 1-to-1 to ORM rows."""

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Inline citations
# ---------------------------------------------------------------------------


class CitationRead(BaseModel):
    """
    One inline citation as stored in ``ChatMessage.citations`` and surfaced
    to the frontend.  The route layer is responsible for renaming the RAG
    tool's ``"source"`` key to ``"url"`` before persisting (see
    ``api/routes/chatbot.py``).
    """

    n: int = Field(..., description="1-based citation index matching the [n] marker in the reply text.")
    title: str
    url: str


# ---------------------------------------------------------------------------
# Chat sessions
# ---------------------------------------------------------------------------


class ChatSessionCreate(BaseModel):
    """Body for POST /chatbot/sessions."""

    title: str = Field(default="New conversation", max_length=255)


class ChatSessionRead(_ORMModel):
    """Read representation of a ``ChatSession`` row."""

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Chat messages
# ---------------------------------------------------------------------------


class SendMessageRequest(BaseModel):
    """Body for POST /chatbot/sessions/{session_id}/messages."""

    content: str = Field(..., min_length=1, max_length=20_000, description="The user's chat message text.")


class ChatMessageRead(_ORMModel):
    """
    Read representation of a ``ChatMessage`` row.

    ``suggested_followups`` is a transient, generation-time-only field —
    the pipeline's ``draft_output["suggested_followups"]`` list is attached
    here by the route layer when first returning the assistant's reply, but
    is NOT persisted to the database and will be ``[]`` on subsequent reads.
    """

    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    citations: list[CitationRead] = Field(default_factory=list)
    intent: str | None = None
    action_result: dict[str, Any] = Field(default_factory=dict)
    confidence_score: float | None = None
    created_at: datetime
    updated_at: datetime

    # Transient — populated by route layer at generation time only.
    suggested_followups: list[str] = Field(default_factory=list)


class ChatTurnResponse(BaseModel):
    """
    Full response for the ``POST .../messages`` endpoint: both the user
    message that was persisted AND the assistant reply that was generated,
    so the frontend can update its conversation view in a single round-trip.
    """

    user_message: ChatMessageRead
    assistant_message: ChatMessageRead


# ---------------------------------------------------------------------------
# Agent memory — transparency / control endpoints
# ---------------------------------------------------------------------------


class AgentMemoryRead(_ORMModel):
    """
    Read representation of one ``AgentMemory`` row — surfaced by
    ``GET /chatbot/memory`` so users can see (and delete) what the system
    remembers about them.
    """

    id: uuid.UUID
    namespace: str = Field(..., description="Memory namespace, e.g. 'career_goals', 'chat_preferences'.")
    key: str
    value: dict[str, Any]
    updated_at: datetime
