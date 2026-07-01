"""
scripts/seed.py
================
Seeds the database with initial demo data for local development and testing.

What this file does:
  - Creates a demo user account you can log in with immediately after setup
  - Creates a demo profile with a handful of skills
  - Creates two sample saved jobs (with real Profile Match Rating scores)
  - Is idempotent: running it again when the demo user already exists is a no-op

How to run:
  cd backend && uv run python scripts/seed.py     (or `make seed` from the root)

Prerequisites:
  - Database must be running (postgres container or local install)
  - Migrations must have been applied (`uv run alembic upgrade head`)
  - The .env file must be configured with DATABASE_URL

Depends on:
  - app/db/session.py for the database connection
  - app/db/models/ for the ORM model classes
  - app/core/security.py for password hashing
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python's import path so we can import app modules.
# This is needed because this script lives in scripts/ (not inside the app package).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.logging import get_logger  # noqa: E402

logger = get_logger(__name__)

# Well-known demo credentials — safe to log because they are not secret.
DEMO_EMAIL = "demo@careerkundi.com"
DEMO_PASSWORD = "demo1234"

# Skills we put on the demo profile. These drive the match scores below.
DEMO_SKILLS = ["Python", "FastAPI", "React", "TypeScript", "PostgreSQL", "Docker"]

# Two sample jobs. Their `extracted_skills` overlap the demo profile to varying
# degrees, so the seeded Profile Match Rating badges show meaningful values.
DEMO_JOBS = [
    {
        "title": "Senior Backend Engineer",
        "company_name": "Acme Cloud",
        "location": "Remote",
        "employment_type": "full_time",
        "is_remote": True,
        "extracted_skills": [
            {"skill": "Python", "importance": "critical"},
            {"skill": "FastAPI", "importance": "high"},
            {"skill": "PostgreSQL", "importance": "high"},
            {"skill": "Kubernetes", "importance": "medium"},
        ],
    },
    {
        "title": "Frontend Engineer",
        "company_name": "Bright Apps",
        "location": "Berlin, DE",
        "employment_type": "full_time",
        "is_remote": False,
        "extracted_skills": [
            {"skill": "React", "importance": "critical"},
            {"skill": "TypeScript", "importance": "high"},
            {"skill": "GraphQL", "importance": "nice-to-have"},
        ],
    },
]


async def seed() -> None:
    """Create the demo user, profile, skills, and saved jobs (idempotent)."""
    # Imported here (not at module top) to avoid circular imports at import time.
    from sqlalchemy import select

    from app.core.security import hash_password
    from app.db.models.job import SavedJob
    from app.db.models.profile import Profile, Skill
    from app.db.models.user import User
    from app.db.session import async_session_factory
    from app.services.matching import compute_match_score

    async with async_session_factory() as session:
        existing = await session.execute(select(User).where(User.email == DEMO_EMAIL))
        if existing.scalar_one_or_none() is not None:
            logger.info("seed_skipped", reason="demo user already exists", email=DEMO_EMAIL)
            return

        # --- User ------------------------------------------------------------
        user = User(
            email=DEMO_EMAIL,
            hashed_password=hash_password(DEMO_PASSWORD),
            full_name="Demo User",
            is_email_verified=True,
        )
        session.add(user)
        await session.flush()  # assigns user.id without committing yet

        # --- Profile + skills ------------------------------------------------
        profile = Profile(
            user_id=user.id,
            professional_headline="Full-Stack Engineer",
            bio_summary="Demo profile seeded for local development and testing.",
        )
        session.add(profile)
        await session.flush()  # assigns profile.id

        for index, skill_name in enumerate(DEMO_SKILLS):
            session.add(
                Skill(profile_id=profile.id, name=skill_name, skill_type="technical", order_index=index)
            )

        # --- Saved jobs (with computed match scores) -------------------------
        user_skills = set(DEMO_SKILLS)
        for job in DEMO_JOBS:
            session.add(
                SavedJob(
                    user_id=user.id,
                    import_method="manual",
                    status="saved",
                    title=job["title"],
                    company_name=job["company_name"],
                    location=job["location"],
                    employment_type=job["employment_type"],
                    is_remote=job["is_remote"],
                    description_raw=f"{job['title']} at {job['company_name']} — seeded demo job.",
                    extracted_skills=job["extracted_skills"],
                    match_score=compute_match_score(user_skills, job["extracted_skills"]),
                )
            )

        await session.commit()

    logger.info(
        "seed_completed",
        email=DEMO_EMAIL,
        password=DEMO_PASSWORD,
        skills=len(DEMO_SKILLS),
        jobs=len(DEMO_JOBS),
        message="Log in with the demo credentials above.",
    )


if __name__ == "__main__":
    asyncio.run(seed())
