"""
api/routes/badges.py
======================
Badge gallery and achievement endpoints.

GET  /badges/definitions               All badge definitions (public catalogue)
GET  /badges/me                        Current user's badge progress (all)
GET  /badges/me/earned                 Only earned badges
GET  /badges/me/pending-celebrations   Newly earned, not yet shown in UI
POST /badges/me/celebrations/{badge_id}/dismiss  Mark celebration as shown
POST /badges/me/mark-offer             User marks they received a job offer (legendary badge)
GET  /badges/me/stats                  Summary stats (earned count, rarity breakdown)
"""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.models.badges import BadgeDefinition, UserBadge
from app.db.models.user import User
from app.db.session import get_db
from app.services.badges import (
    fire_event,
    get_pending_celebrations,
    get_user_badges,
    mark_celebration_shown,
)

router = APIRouter(prefix="/badges", tags=["badges"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class BadgeDefinitionRead(BaseModel):
    id: str
    name: str
    description: str
    category: str
    icon: str
    color_swatch: str
    rarity: str
    condition_type: str
    condition_metric: str
    condition_target: int
    display_order: int

    model_config = {"from_attributes": True}


class UserBadgeRead(BaseModel):
    badge_id: str
    progress: int
    is_earned: bool
    earned_at: datetime | None
    celebration_shown: bool
    pct_complete: float
    badge: BadgeDefinitionRead

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_badge(cls, ub: UserBadge) -> "UserBadgeRead":
        return cls(
            badge_id=ub.badge_id,
            progress=ub.progress,
            is_earned=ub.is_earned,
            earned_at=ub.earned_at,
            celebration_shown=ub.celebration_shown,
            pct_complete=ub.pct_complete,
            badge=BadgeDefinitionRead.model_validate(ub.badge_definition),
        )


class BadgeStatsRead(BaseModel):
    total_earned: int
    total_available: int
    common_earned: int
    uncommon_earned: int
    rare_earned: int
    epic_earned: int
    legendary_earned: int
    completion_pct: float


# ---------------------------------------------------------------------------
# Helper: ensure a UserBadge row exists for every definition
# ---------------------------------------------------------------------------

async def _hydrate_all_badges(db: AsyncSession, user_id: uuid.UUID) -> list[UserBadge]:
    """
    Return UserBadge rows for every badge in the catalogue.
    Creates a placeholder row (progress=0, is_earned=False) for badges the
    user hasn't interacted with yet — this lets the UI render locked states
    without extra client logic.
    """
    # All definitions
    defs_result = await db.execute(
        select(BadgeDefinition).order_by(BadgeDefinition.display_order)
    )
    defs = list(defs_result.scalars())

    # Existing user badge rows
    ub_result = await db.execute(
        select(UserBadge)
        .where(UserBadge.user_id == user_id)
        .options(selectinload(UserBadge.badge_definition))
    )
    existing = {ub.badge_id: ub for ub in ub_result.scalars()}

    result_list: list[UserBadge] = []
    for defn in defs:
        if defn.id in existing:
            ub = existing[defn.id]
            # Manually attach definition to avoid lazy-load
            ub.badge_definition = defn
            result_list.append(ub)
        else:
            # Synthetic placeholder — NOT flushed to DB
            ub = UserBadge(
                user_id=user_id,
                badge_id=defn.id,
                progress=0,
                is_earned=False,
                celebration_shown=True,
            )
            ub.badge_definition = defn
            result_list.append(ub)

    return result_list


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/definitions", response_model=list[BadgeDefinitionRead])
async def list_badge_definitions(
    db: AsyncSession = Depends(get_db),
) -> list[BadgeDefinitionRead]:
    """Public badge catalogue — no auth required."""
    result = await db.execute(
        select(BadgeDefinition).order_by(BadgeDefinition.display_order)
    )
    return [BadgeDefinitionRead.model_validate(d) for d in result.scalars()]


@router.get("/me", response_model=list[UserBadgeRead])
async def get_my_badges(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[UserBadgeRead]:
    """All badges with progress — including locked ones (progress=0)."""
    badges = await _hydrate_all_badges(db, user.id)
    return [UserBadgeRead.from_orm_with_badge(b) for b in badges]


@router.get("/me/earned", response_model=list[UserBadgeRead])
async def get_earned_badges(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[UserBadgeRead]:
    earned = await get_user_badges(db, user.id)
    return [
        UserBadgeRead.from_orm_with_badge(b)
        for b in earned
        if b.is_earned
    ]


@router.get("/me/pending-celebrations", response_model=list[UserBadgeRead])
async def get_pending_celebration_badges(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[UserBadgeRead]:
    """
    Newly earned badges that haven't had their celebration animation shown yet.
    The frontend polls this on page load / focus. After showing the animation,
    call POST /dismiss to clear the flag.
    """
    badges = await get_pending_celebrations(db, user.id)
    return [UserBadgeRead.from_orm_with_badge(b) for b in badges]


@router.post("/me/celebrations/{badge_id}/dismiss", status_code=204)
async def dismiss_celebration(
    badge_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(UserBadge)
        .where(UserBadge.user_id == user.id, UserBadge.badge_id == badge_id)
        .options(selectinload(UserBadge.badge_definition))
    )
    ub = result.scalar_one_or_none()
    if not ub:
        raise HTTPException(status_code=404, detail="Badge not found.")
    await mark_celebration_shown(db, ub)
    await db.commit()


@router.post("/me/mark-offer", response_model=dict)
async def mark_job_offer(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """User marks that they received a job offer — triggers the legendary 'Mission Complete' badge."""
    newly_earned = await fire_event(db, user.id, "job_offer_received")
    await db.commit()
    return {"newly_earned_badges": newly_earned}


@router.get("/me/stats", response_model=BadgeStatsRead)
async def get_badge_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BadgeStatsRead:
    badges = await _hydrate_all_badges(db, user.id)
    total = len(badges)
    earned = [b for b in badges if b.is_earned]
    rarity_counts = {}
    for b in earned:
        r = b.badge_definition.rarity if b.badge_definition else "common"
        rarity_counts[r] = rarity_counts.get(r, 0) + 1

    return BadgeStatsRead(
        total_earned=len(earned),
        total_available=total,
        common_earned=rarity_counts.get("common", 0),
        uncommon_earned=rarity_counts.get("uncommon", 0),
        rare_earned=rarity_counts.get("rare", 0),
        epic_earned=rarity_counts.get("epic", 0),
        legendary_earned=rarity_counts.get("legendary", 0),
        completion_pct=round(len(earned) / total * 100, 1) if total else 0.0,
    )
