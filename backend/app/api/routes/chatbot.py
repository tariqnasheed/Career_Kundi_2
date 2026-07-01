"""
api/routes/chatbot.py
=========================
AI Assistant Chatbot (§4.7) endpoints.

Thin HTTP wrapper around ``app.agents.chatbot.graph.run_chat_turn_pipeline()``
plus straightforward ORM persistence.  No agent logic, prompting, RAG,
GraphRAG, or memory inference happens here — all of that lives in
``app/agents/chatbot/``.

This module's specific responsibilities (the "route layer" side of the
platform-wide invariant that agents never touch the database):

  1. **Loading context** — before the graph runs, the route layer loads
     recent conversation history, cross-session long-term memory, and a
     flattened snapshot of the user's profile/jobs/roadmaps/CVs so agents
     receive plain dicts rather than database handles.

  2. **Persisting results** — after the graph runs, the route layer persists
     the user message (if not yet saved), the assistant message (with its
     citations, intent, and action_result), memory_updates (upserted into
     ``AgentMemory``), and the CostMonitor usage record.

  3. **Citation key rename** — ``app/tools/rag.py`` returns citations with a
     ``"source"`` key; ``ChatMessage.citations`` documents them as
     ``{"n", "title", "url"}``.  The rename happens here, not in any agent.

Endpoint summary
----------------
POST   /api/v1/chatbot/sessions                                — Start a new chat session.
GET    /api/v1/chatbot/sessions                                — List user's sessions (newest first).
GET    /api/v1/chatbot/sessions/{session_id}                   — Get a session with its full message history.
DELETE /api/v1/chatbot/sessions/{session_id}                   — Delete a session (cascades to messages).
POST   /api/v1/chatbot/sessions/{session_id}/messages          — Send a user message, run the pipeline, return both user + assistant messages.
POST   /api/v1/chatbot/sessions/{session_id}/messages/{msg_id}/redo  — Regenerate the assistant reply to a given user message.
GET    /api/v1/chatbot/memory                                  — List the user's cross-session long-term memory facts.
DELETE /api/v1/chatbot/memory/{namespace}/{key}                — Forget a specific long-term memory fact.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.chatbot.graph import run_chat_turn_pipeline
from app.api.deps import get_current_user
from app.api.routes.profile import _get_or_create_profile
from app.core.errors import NotFoundError
from app.db.models.chat import ChatMessage, ChatSession
from app.db.models.cv import GeneratedCV
from app.db.models.job import SavedJob
from app.db.models.memory import AgentMemory
from app.db.models.profile import Profile
from app.db.models.roadmap import Roadmap, RoadmapMilestone, RoadmapSkill
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.chatbot import (
    AgentMemoryRead,
    ChatMessageRead,
    ChatSessionCreate,
    ChatSessionRead,
    ChatTurnResponse,
    SendMessageRequest,
)

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

# How many recent messages to include in session_snapshot.recent_messages.
# Large enough to give the MemoryAgent useful conversation context;
# small enough to avoid bloating the executor prompt.
_RECENT_MESSAGE_LIMIT = 12


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _get_owned_session(db: AsyncSession, user: User, session_id: uuid.UUID) -> ChatSession:
    """
    Fetch a ``ChatSession`` this user actually owns, with messages
    eager-loaded (ordered by ``created_at`` ASC), or raise ``NotFoundError``
    so the API never leaks whether another user's session exists.
    """
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.id == session_id, ChatSession.user_id == user.id)
        .options(selectinload(ChatSession.messages))
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise NotFoundError("Chat session not found.")
    return session


async def _load_long_term_memory(db: AsyncSession, user_id: uuid.UUID) -> dict[str, dict[str, Any]]:
    """
    Load all ``AgentMemory`` rows for this user and flatten them into the
    ``{namespace: {key: value}}`` dict the MemoryAgent expects.  Returns an
    empty dict for a brand-new user with no stored memory yet.
    """
    result = await db.execute(select(AgentMemory).where(AgentMemory.user_id == user_id))
    rows = result.scalars().all()
    memory: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.namespace not in memory:
            memory[row.namespace] = {}
        memory[row.namespace][row.key] = row.value
    return memory


async def _build_user_context_snapshot(db: AsyncSession, user: User) -> dict[str, Any]:
    """
    Assemble the flat ``user_context_snapshot`` dict the ActionDispatchAgent
    reads for data-bearing intents (action_request, job_search_guidance,
    roadmap_guidance, cv_feedback, profile_help).

    All database I/O happens here — agents NEVER load ORM rows themselves.

    Keys produced (all optional — set to sensible defaults if not populated):
        saved_job_count        int
        recent_job_titles      list[str]   up to 3 most-recent job titles
        active_target_role     str | None  target_role of most-recently-
                                            updated roadmap, if any
        completed_skill_count  int | None
        total_skill_count      int | None
        cv_count               int
        profile_completeness   float       0–100 from Profile.completeness_score()
        missing_sections       list[str]   human-readable names of empty profile sections
        user_full_name         str | None
        user_email             str
    """
    snapshot: dict[str, Any] = {
        "user_email": user.email,
        "user_full_name": getattr(user, "full_name", None),
    }

    # --- Saved jobs -------------------------------------------------------
    jobs_result = await db.execute(
        select(SavedJob)
        .where(SavedJob.user_id == user.id)
        .order_by(SavedJob.created_at.desc())
        .limit(3)
    )
    recent_jobs = list(jobs_result.scalars().all())

    # Total count via a separate count query (avoid fetching all rows).
    count_result = await db.execute(select(SavedJob).where(SavedJob.user_id == user.id))
    all_jobs = count_result.scalars().all()
    snapshot["saved_job_count"] = len(all_jobs)
    snapshot["recent_job_titles"] = [j.title for j in recent_jobs if j.title]

    # --- CV count ----------------------------------------------------------
    cv_result = await db.execute(select(GeneratedCV).where(GeneratedCV.user_id == user.id))
    snapshot["cv_count"] = len(cv_result.scalars().all())

    # --- Active roadmap ----------------------------------------------------
    roadmap_result = await db.execute(
        select(Roadmap)
        .where(Roadmap.user_id == user.id)
        .options(selectinload(Roadmap.milestones).selectinload(RoadmapMilestone.skills))
        .order_by(Roadmap.updated_at.desc())
        .limit(1)
    )
    active_roadmap = roadmap_result.scalar_one_or_none()
    if active_roadmap:
        snapshot["active_target_role"] = active_roadmap.target_role
        all_skills: list[RoadmapSkill] = [
            skill
            for milestone in active_roadmap.milestones
            for skill in milestone.skills
        ]
        snapshot["total_skill_count"] = len(all_skills)
        snapshot["completed_skill_count"] = sum(1 for s in all_skills if s.status == "completed")
    else:
        snapshot["active_target_role"] = None
        snapshot["total_skill_count"] = None
        snapshot["completed_skill_count"] = None

    # --- Profile completeness + missing sections ----------------------------
    profile = await _get_or_create_profile(db, user)
    snapshot["profile_completeness"] = profile.completeness_score()
    snapshot["missing_sections"] = _detect_missing_profile_sections(profile)

    return snapshot


def _detect_missing_profile_sections(profile: Profile) -> list[str]:
    """
    Return a list of human-readable section names that the user hasn't
    filled in yet.  Used by the ActionDispatchAgent to give the CV feedback
    / profile help executor grounded, specific guidance ("Your Skills
    section is empty") rather than generic advice.
    """
    missing: list[str] = []
    if not profile.professional_headline:
        missing.append("Professional Headline")
    if not profile.bio_summary:
        missing.append("Bio / Professional Summary")
    if not profile.work_experiences:
        missing.append("Work Experience")
    if not profile.educations:
        missing.append("Education")
    if not profile.skills:
        missing.append("Skills")
    if not profile.projects:
        missing.append("Projects")
    if not (profile.linkedin_url or profile.github_url or profile.portfolio_url):
        missing.append("Professional Links (LinkedIn / GitHub / Portfolio)")
    return missing


def _build_session_snapshot(session: ChatSession) -> dict[str, Any]:
    """
    Flatten a ``ChatSession`` + its loaded messages into the plain dict the
    MemoryAgent receives — recent messages only, capped at
    ``_RECENT_MESSAGE_LIMIT`` to keep the executor prompt manageable.
    """
    recent = session.messages[-_RECENT_MESSAGE_LIMIT:] if session.messages else []
    return {
        "session_id": str(session.id),
        "title": session.title,
        "recent_messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in recent
        ],
    }


def _remap_citations(raw_citations: list[dict]) -> list[dict]:
    """
    Rename ``"source"`` → ``"url"`` in the citation dicts returned by
    ``app/tools/rag.py`` so they match the ``{"n", "title", "url"}`` shape
    documented on ``ChatMessage.citations``.  This is the single place in
    the codebase where that rename happens.
    """
    return [
        {"n": c.get("n", i + 1), "title": c.get("title", "Source"), "url": c.get("source", c.get("url", ""))}
        for i, c in enumerate(raw_citations)
    ]


async def _upsert_memory_updates(
    db: AsyncSession, user_id: uuid.UUID, memory_updates: list[dict[str, Any]]
) -> None:
    """
    Persist the MemoryAgent's proposed upserts into ``AgentMemory``.  Each
    update is ``{"namespace": str, "key": str, "value": dict}``.  Existing
    rows (same user_id/namespace/key) are updated in place; new combinations
    produce fresh rows.  Flushes to the session without committing (the
    caller commits alongside the assistant message).
    """
    for update in memory_updates:
        namespace = update.get("namespace", "")
        key = update.get("key", "")
        value = update.get("value", {})
        if not namespace or not key:
            continue

        existing = await db.execute(
            select(AgentMemory).where(
                AgentMemory.user_id == user_id,
                AgentMemory.namespace == namespace,
                AgentMemory.key == key,
            )
        )
        row = existing.scalar_one_or_none()
        if row is not None:
            row.value = value
        else:
            db.add(AgentMemory(user_id=user_id, namespace=namespace, key=key, value=value))
    await db.flush()


# ---------------------------------------------------------------------------
# Session CRUD
# ---------------------------------------------------------------------------


@router.post("/sessions", response_model=ChatSessionRead, status_code=201)
async def create_session(
    payload: ChatSessionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatSession:
    """
    Start a new chat session for this user.

    A session is a named conversation thread; all messages sent within it
    share a common ``session_id`` so the MemoryAgent can load them as prior
    context.  Users can have multiple concurrent sessions (e.g. one for
    general career chat, one specifically about a job application).
    """
    session = ChatSession(user_id=user.id, title=payload.title)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/sessions", response_model=list[ChatSessionRead])
async def list_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ChatSession]:
    """All chat sessions for this user, newest first."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .order_by(ChatSession.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/sessions/{session_id}", response_model=ChatSessionRead)
async def get_session(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatSession:
    """Fetch one session with its full message history (newest last)."""
    return await _get_owned_session(db, user, session_id)


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Delete a session and all its messages.  Cascade is defined on the
    ORM relationship so no manual message deletion is required.
    """
    session = await _get_owned_session(db, user, session_id)
    await db.delete(session)
    await db.commit()
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Send message — the main pipeline endpoint
# ---------------------------------------------------------------------------


@router.post("/sessions/{session_id}/messages", response_model=ChatTurnResponse, status_code=201)
async def send_message(
    session_id: uuid.UUID,
    payload: SendMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatTurnResponse:
    """
    Send a user message, run the 7-node chatbot pipeline, and return both
    the persisted user message and the generated assistant reply.

    Processing order (all within this single request):
      1. Persist the user's ChatMessage row (role="user").
      2. Reload the session with the new message now included in history.
      3. Load long-term memory and user-context snapshot from the DB.
      4. Run run_chat_turn_pipeline() with the assembled context.
      5. Persist the assistant's ChatMessage (with remapped citations,
         intent, action_result, and confidence_score).
      6. Upsert MemoryAgent's proposed memory_updates into AgentMemory.
      7. Persist the CostMonitor usage record.
      8. Commit everything (two commits: once for messages + memory, once
         for the cost-monitor flush per the established double-commit pattern).
      9. Return ChatTurnResponse with suggested_followups attached to the
         assistant message (transient — not stored in the DB).
    """
    session = await _get_owned_session(db, user, session_id)

    # Step 1 — Persist the user message so it appears in session history
    # before the pipeline loads recent_messages (the MemoryAgent sees it as
    # the current turn in the conversation context it builds).
    user_msg = ChatMessage(session_id=session.id, role="user", content=payload.content)
    db.add(user_msg)
    await db.commit()
    await db.refresh(user_msg)

    # Step 2 — Reload session with messages (includes the just-persisted row).
    session = await _get_owned_session(db, user, session_id)
    session_snapshot = _build_session_snapshot(session)

    # Step 3 — Load memory + user context (pure DB reads, no agent involved).
    long_term_memory = await _load_long_term_memory(db, user.id)
    user_context_snapshot = await _build_user_context_snapshot(db, user)

    # Step 4 — Run the pipeline.
    result = await run_chat_turn_pipeline(
        user_id=str(user.id),
        raw_input=payload.content,
        session_snapshot=session_snapshot,
        long_term_memory=long_term_memory,
        user_context_snapshot=user_context_snapshot,
    )
    final_state = result["state"]
    cost_monitor = result["cost_monitor"]

    draft = final_state.get("draft_output") or {}
    reply_text = draft.get("reply", "(no reply generated)")
    suggested_followups: list[str] = draft.get("suggested_followups", [])

    # Step 5 — Persist the assistant message.
    # Remap citations "source" → "url" so they match the schema documented
    # on ChatMessage.citations: [{"n": int, "title": str, "url": str}].
    remapped_citations = _remap_citations(final_state.get("citations") or [])
    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=reply_text,
        citations=remapped_citations,
        intent=final_state.get("intent"),
        action_result=final_state.get("action_result") or {},
        confidence_score=final_state.get("confidence_score"),
    )
    db.add(assistant_msg)

    # Step 6 — Upsert MemoryAgent's proposed memory updates.
    await _upsert_memory_updates(db, user.id, final_state.get("memory_updates") or [])

    # Commit messages + memory together.
    await db.commit()
    await db.refresh(user_msg)
    await db.refresh(assistant_msg)

    # Step 7 — Persist CostMonitor usage record (flush only; explicit commit below).
    await cost_monitor.persist(db, user_id=str(user.id), model_used=final_state.get("model_tier_used", "unknown"))
    await db.commit()  # CostMonitor.persist() only flushes — commit explicitly so the usage record survives session close

    # Build the response — attach suggested_followups to the assistant read
    # model (it's a transient field with no ORM column, not returned by
    # model_validate alone).
    user_read = ChatMessageRead.model_validate(user_msg)
    assistant_read = ChatMessageRead.model_validate(assistant_msg)
    assistant_read.suggested_followups = suggested_followups

    return ChatTurnResponse(user_message=user_read, assistant_message=assistant_read)


# ---------------------------------------------------------------------------
# Redo — regenerate the assistant reply to a given user message
# ---------------------------------------------------------------------------


@router.post(
    "/sessions/{session_id}/messages/{message_id}/redo",
    response_model=ChatMessageRead,
)
async def redo_message(
    session_id: uuid.UUID,
    message_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatMessageRead:
    """
    Regenerate the assistant's reply to a specific user message (the "Re-do"
    button hinted at in ``db/models/chat.py``'s module docstring and exposed
    in the Dashboard's Recent Activity Feed).

    ``message_id`` must be the ID of a USER message (role="user") within a
    session this user owns.  The assistant reply immediately following it in
    chronological order is updated in place rather than inserting a new row,
    so existing frontend message IDs remain stable.

    If no assistant message follows yet (e.g. the pipeline failed on the
    first attempt), a new assistant message row is created.
    """
    session = await _get_owned_session(db, user, session_id)

    # Locate the target user message within this session's loaded messages
    # (already ordered by created_at ASC via the ORM relationship).
    target_user_msg: ChatMessage | None = None
    for i, msg in enumerate(session.messages):
        if msg.id == message_id:
            if msg.role != "user":
                raise NotFoundError("Specified message is not a user message.")
            target_user_msg = msg
            # Look for the assistant message that immediately follows.
            assistant_msg: ChatMessage | None = None
            if i + 1 < len(session.messages) and session.messages[i + 1].role == "assistant":
                assistant_msg = session.messages[i + 1]
            break

    if target_user_msg is None:
        raise NotFoundError("Message not found in this session.")

    # Reload context fresh so the redo uses up-to-date memory / profile data.
    long_term_memory = await _load_long_term_memory(db, user.id)
    user_context_snapshot = await _build_user_context_snapshot(db, user)

    # Build session_snapshot from the messages UP TO AND INCLUDING the target
    # user message (exclude any messages that came after it, since those
    # belong to a different conversational branch that the redo replaces).
    msg_index = session.messages.index(target_user_msg)
    slice_for_context = session.messages[: msg_index + 1]
    session_snapshot = {
        "session_id": str(session.id),
        "title": session.title,
        "recent_messages": [
            {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
            for m in slice_for_context[-_RECENT_MESSAGE_LIMIT:]
        ],
    }

    result = await run_chat_turn_pipeline(
        user_id=str(user.id),
        raw_input=target_user_msg.content,
        session_snapshot=session_snapshot,
        long_term_memory=long_term_memory,
        user_context_snapshot=user_context_snapshot,
    )
    final_state = result["state"]
    cost_monitor = result["cost_monitor"]

    draft = final_state.get("draft_output") or {}
    reply_text = draft.get("reply", "(no reply generated)")
    suggested_followups: list[str] = draft.get("suggested_followups", [])
    remapped_citations = _remap_citations(final_state.get("citations") or [])

    if assistant_msg is not None:
        # Update existing assistant message in place.
        assistant_msg.content = reply_text
        assistant_msg.citations = remapped_citations
        assistant_msg.intent = final_state.get("intent")
        assistant_msg.action_result = final_state.get("action_result") or {}
        assistant_msg.confidence_score = final_state.get("confidence_score")
    else:
        # First-time assistant reply (e.g. original pipeline failed).
        assistant_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=reply_text,
            citations=remapped_citations,
            intent=final_state.get("intent"),
            action_result=final_state.get("action_result") or {},
            confidence_score=final_state.get("confidence_score"),
        )
        db.add(assistant_msg)

    await _upsert_memory_updates(db, user.id, final_state.get("memory_updates") or [])
    await db.commit()
    await db.refresh(assistant_msg)

    await cost_monitor.persist(db, user_id=str(user.id), model_used=final_state.get("model_tier_used", "unknown"))
    await db.commit()  # CostMonitor.persist() only flushes — commit explicitly so the usage record survives session close

    assistant_read = ChatMessageRead.model_validate(assistant_msg)
    assistant_read.suggested_followups = suggested_followups
    return assistant_read


# ---------------------------------------------------------------------------
# Memory transparency / control
# ---------------------------------------------------------------------------


@router.get("/memory", response_model=list[AgentMemoryRead])
async def list_memory(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AgentMemory]:
    """
    List all long-term memory facts the platform has stored about this user,
    grouped logically by namespace.  Provides the transparency layer §2
    "Agentic Memory" requires — users must be able to see and control what
    the system knows about them.
    """
    result = await db.execute(
        select(AgentMemory)
        .where(AgentMemory.user_id == user.id)
        .order_by(AgentMemory.namespace, AgentMemory.key)
    )
    return list(result.scalars().all())


@router.delete("/memory/{namespace}/{key}", status_code=204)
async def forget_memory(
    namespace: str,
    key: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Delete one specific memory fact (identified by namespace + key) so the
    user can correct or remove things the system has learned about them.
    GDPR "right to erasure" at the granular memory level.
    """
    result = await db.execute(
        select(AgentMemory).where(
            AgentMemory.user_id == user.id,
            AgentMemory.namespace == namespace,
            AgentMemory.key == key,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise NotFoundError(f"Memory fact '{namespace}/{key}' not found.")
    await db.delete(row)
    await db.commit()
    return Response(status_code=204)
