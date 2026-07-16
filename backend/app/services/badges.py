"""
services/badges.py
==================
Badge event system.  Route handlers (and agent pipelines via the route layer)
call `fire_event(db, user_id, metric, value)` after any action that can
award a badge.

Public API
----------
  seed_badge_definitions(db)          Idempotent upsert of all BADGE_DEFINITIONS
  fire_event(db, user_id, metric, value=1) → list[str]  newly-earned badge IDs
  get_user_badges(db, user_id)        All UserBadge rows for a user
  mark_celebration_shown(db, ub)      Clear the pending celebration flag

Design decisions
----------------
  - All DB access is synchronous-safe but called inside async routes via
    `await db.run_sync(...)` pattern when needed — here we expose sync
    helpers that are called inline within the already-open async session.
  - `fire_event` returns the list of newly-earned badge IDs so the route can
    include them in the API response (the UI can trigger celebration animations).
  - We never raise exceptions inside fire_event — badge award failures are
    logged and swallowed so they never block the primary user action.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.data.badges_seed import BADGE_DEFINITIONS
from app.db.models.badges import BadgeDefinition, UserBadge

log = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------

_BADGE_MUTABLE_FIELDS = (
    "name",
    "description",
    "icon",
    "color_swatch",
    "rarity",
    "condition_type",
    "condition_metric",
    "condition_target",
    "condition_score_min",
    "display_order",
)


async def seed_badge_definitions(db: AsyncSession) -> dict[str, int]:
    """
    Idempotent upsert of the static badge catalogue.

    Called once at application startup from main.py lifespan.

    Performance (0053-F15): one SELECT of existing rows, then insert/update
    only when needed. When the catalogue is already current, this is a
    skip-safe no-op (no commit, no per-badge round trips).
    """
    result = await db.execute(select(BadgeDefinition))
    existing_by_id = {row.id: row for row in result.scalars().all()}

    inserted = 0
    updated = 0
    unchanged = 0

    for defn in BADGE_DEFINITIONS:
        badge_id = defn["id"]
        existing = existing_by_id.get(badge_id)
        if existing is None:
            row = BadgeDefinition(**{k: v for k, v in defn.items() if v is not None})
            db.add(row)
            inserted += 1
            continue

        changed = False
        for field in _BADGE_MUTABLE_FIELDS:
            if field not in defn:
                continue
            new_value = defn[field]
            if getattr(existing, field) != new_value:
                setattr(existing, field, new_value)
                changed = True
        if changed:
            updated += 1
        else:
            unchanged += 1

    if inserted or updated:
        await db.commit()

    summary = {
        "inserted": inserted,
        "updated": updated,
        "unchanged": unchanged,
        "count": len(BADGE_DEFINITIONS),
    }
    log.info("badge_definitions_seeded", **summary)
    return summary


# ---------------------------------------------------------------------------
# Progress helpers
# ---------------------------------------------------------------------------

async def _get_or_create_user_badge(
    db: AsyncSession, user_id: str, badge_id: str
) -> UserBadge:
    result = await db.execute(
        select(UserBadge)
        .where(UserBadge.user_id == user_id, UserBadge.badge_id == badge_id)
        .options(selectinload(UserBadge.badge_definition))
    )
    ub = result.scalar_one_or_none()
    if ub is None:
        ub = UserBadge(user_id=user_id, badge_id=badge_id, progress=0)
        db.add(ub)
        await db.flush()
        # Re-fetch with definition
        await db.refresh(ub, ["badge_definition"])
    return ub


# ---------------------------------------------------------------------------
# Main event fire
# ---------------------------------------------------------------------------

async def fire_event(
    db: AsyncSession,
    user_id: Any,
    metric: str,
    value: int | float = 1,
) -> list[str]:
    """
    Record progress for `metric` and award any newly-qualifying badges.

    Parameters
    ----------
    metric   Internal metric name matching BadgeDefinition.condition_metric
    value    The new measurement value:
             - boolean: ignored (always treated as 1)
             - count:   increment amount (usually 1)
             - streak:  new streak length
             - score:   the raw score (0-100)

    Returns
    -------
    List of badge IDs that were earned for the first time by this call.
    Empty list if no badge was newly earned (the common case).
    """
    newly_earned: list[str] = []
    try:
        # Find all badge definitions that track this metric
        result = await db.execute(
            select(BadgeDefinition).where(BadgeDefinition.condition_metric == metric)
        )
        definitions = result.scalars().all()
        if not definitions:
            return []

        for defn in definitions:
            ub = await _get_or_create_user_badge(db, user_id, defn.id)
            if ub.is_earned:
                continue  # already have it — nothing to do

            # Update progress according to condition type
            earned = False
            if defn.condition_type == "boolean":
                ub.progress = 1
                earned = True

            elif defn.condition_type == "count":
                ub.progress += int(value)
                earned = ub.progress >= defn.condition_target

            elif defn.condition_type == "streak":
                ub.progress = int(value)
                ub.last_activity_date = datetime.now(timezone.utc)
                earned = ub.progress >= defn.condition_target

            elif defn.condition_type == "score":
                # For score badges: take the *best* score seen
                ub.progress = max(ub.progress, int(value))
                min_score = defn.condition_score_min or float(defn.condition_target)
                earned = float(value) >= min_score

            if earned:
                ub.is_earned = True
                ub.earned_at = datetime.now(timezone.utc)
                ub.celebration_shown = False
                newly_earned.append(defn.id)
                log.info("badge_earned", user_id=str(user_id), badge_id=defn.id)

        await db.flush()

        # Check "all categories" meta-badge after any individual badge is earned
        if newly_earned:
            await _check_all_categories_badge(db, user_id)

    except Exception:
        log.exception("badge_fire_event_error", metric=metric, user_id=str(user_id))

    return newly_earned


async def _check_all_categories_badge(db: AsyncSession, user_id: Any) -> None:
    """Award the legendary Champion badge if user has earned ≥1 badge from every category."""
    champion_id = "career_kundi_champion"
    champion = await db.get(UserBadge, {"user_id": user_id, "badge_id": champion_id})
    if champion and champion.is_earned:
        return

    # Get all distinct categories from definitions
    all_cats_result = await db.execute(select(BadgeDefinition.category).distinct())
    all_cats = {r for r in all_cats_result.scalars() if r != "learning_challenge"}
    # (learning_challenge houses the champion badge itself — skip it in the check)

    # Get categories where user has ≥1 earned badge
    earned_result = await db.execute(
        select(BadgeDefinition.category)
        .join(UserBadge, UserBadge.badge_id == BadgeDefinition.id)
        .where(
            UserBadge.user_id == user_id,
            UserBadge.is_earned == True,       # noqa: E712
            BadgeDefinition.id != champion_id,
        )
        .distinct()
    )
    earned_cats = set(earned_result.scalars())

    if all_cats and all_cats.issubset(earned_cats):
        await fire_event(db, user_id, "all_categories_badge_earned")


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

async def get_user_badges(db: AsyncSession, user_id: Any) -> list[UserBadge]:
    result = await db.execute(
        select(UserBadge)
        .where(UserBadge.user_id == user_id)
        .options(selectinload(UserBadge.badge_definition))
        .order_by(UserBadge.earned_at.desc().nulls_last())
    )
    return list(result.scalars())


async def mark_celebration_shown(db: AsyncSession, user_badge: UserBadge) -> None:
    user_badge.celebration_shown = True
    await db.flush()


async def get_pending_celebrations(db: AsyncSession, user_id: Any) -> list[UserBadge]:
    """Return newly-earned badges whose celebration animation hasn't been shown yet."""
    result = await db.execute(
        select(UserBadge)
        .where(
            UserBadge.user_id == user_id,
            UserBadge.is_earned == True,       # noqa: E712
            UserBadge.celebration_shown == False,  # noqa: E712
        )
        .options(selectinload(UserBadge.badge_definition))
    )
    return list(result.scalars())
