"""
api/routes/job_search.py
=============================
Job Search & Discovery (§4.1) + Interview Pack Generation (§4.2) endpoints.

Every endpoint here is a thin HTTP wrapper around the LangGraph pipelines in
`app.agents.job_search.graph` — no agent logic, prompting, RAG, or
verification happens in this file. The route layer's only jobs are: (1)
authenticate + load/own the right ORM rows, (2) invoke the pipeline, (3)
map the pipeline's plain-dict output onto `SavedJob` columns and persist,
(4) record token-usage accounting via the returned `CostMonitor`.

Endpoint summary
----------------
POST   /api/v1/job-search/parse                          — Resolve a URL or pasted text into a saved, enriched job.
GET    /api/v1/job-search/                                — List the current user's saved jobs.
GET    /api/v1/job-search/{job_id}                        — Fetch one saved job.
DELETE /api/v1/job-search/{job_id}                        — Delete a saved job.
POST   /api/v1/job-search/{job_id}/interview-pack         — Generate (or regenerate) an interview pack for a saved job.
GET    /api/v1/job-search/{job_id}/interview-pack         — Fetch the most recently generated interview pack.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.job_search.graph import run_interview_pack_pipeline, run_job_enrichment_pipeline
from app.api.deps import get_current_user
from app.core.errors import NotFoundError
from app.db.models.job import SavedJob
from app.db.models.profile import Profile, Skill
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.job_search import (
    InterviewPackRead,
    InterviewPackRequest,
    JobParseRequest,
    JobStatusUpdate,
    SavedJobCreate,
    SavedJobRead,
)
from app.services.matching import compute_match_score

router = APIRouter(prefix="/job-search", tags=["job-search"])


async def _get_owned_job(db: AsyncSession, user: User, job_id: uuid.UUID) -> SavedJob:
    """Fetch a `SavedJob` the current user actually owns, or raise `NotFoundError` (never leaks existence of other users' rows)."""
    result = await db.execute(select(SavedJob).where(SavedJob.id == job_id, SavedJob.user_id == user.id))
    job = result.scalar_one_or_none()
    if job is None:
        raise NotFoundError("Saved job not found.")
    return job


async def _user_skill_names(db: AsyncSession, user: User) -> set[str]:
    """Return the set of skill names on the current user's profile (used for match scoring)."""
    result = await db.execute(
        select(Skill.name).join(Profile, Skill.profile_id == Profile.id).where(Profile.user_id == user.id)
    )
    return {row[0] for row in result.all()}


@router.post("/parse", response_model=SavedJobRead, status_code=201)
async def parse_job(
    payload: JobParseRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SavedJob:
    """
    Resolve a job posting (direct URL paste, scraped server-side, or raw
    pasted text) through the full Guardrail -> Planner -> Executor ->
    CrossVerifier -> Reflector pipeline, then persist the structured,
    RAG-grounded, cross-verified result as a new `SavedJob` row.
    """
    result = await run_job_enrichment_pipeline(
        user_id=str(user.id),
        url=payload.url,
        pasted_text=payload.pasted_text,
    )
    final_state = result["state"]
    cost_monitor = result["cost_monitor"]
    source_meta = result["source_meta"]
    draft = final_state.get("draft_output") or {}

    # Profile Match Rating: score how well this job's required skills line up
    # with the skills on the user's profile (0-100, or None if the job lists none).
    match_score = compute_match_score(await _user_skill_names(db, user), draft.get("extracted_skills", []))

    job = SavedJob(
        user_id=user.id,
        source_url=source_meta.get("source_url"),
        source_site=source_meta.get("source_site"),
        import_method=source_meta.get("import_method", "manual"),
        title=draft.get("title") or "Untitled Role",
        company_name=draft.get("company_name"),
        company_url=draft.get("company_url"),
        location=draft.get("location"),
        employment_type=draft.get("employment_type"),
        is_remote=draft.get("is_remote"),
        salary_min=draft.get("salary_min"),
        salary_max=draft.get("salary_max"),
        salary_currency=draft.get("salary_currency"),
        description_raw=final_state.get("job_text", ""),
        responsibilities=draft.get("responsibilities", []),
        requirements=draft.get("requirements", []),
        benefits=draft.get("benefits", []),
        extracted_skills=draft.get("extracted_skills", []),
        company_profile=draft.get("company_profile", {}),
        verification_status=final_state.get("verification_status", "unverified"),
        verification_sources=final_state.get("verification_sources", []),
        match_score=match_score,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    await cost_monitor.persist(db, user_id=str(user.id), model_used=final_state.get("model_tier_used", "unknown"))
    await db.commit()  # CostMonitor.persist() only flushes — commit explicitly so the usage record survives session close

    return job


@router.post("/", response_model=SavedJobRead, status_code=201)
async def save_job(
    payload: SavedJobCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SavedJob:
    """
    Persist a job the user has already reviewed on the client (the "Save Job"
    button on the Job Search page) as a new `SavedJob` row.

    Unlike `POST /parse`, this does NOT re-run the extraction/enrichment
    pipeline — it trusts the reviewed fields the client sends, so any manual
    edits the user made in the "Review extracted data" form are preserved.
    """
    # Profile Match Rating: same 0-100 fit score as the parse flow, computed
    # from the reviewed skills the client is saving.
    match_score = compute_match_score(await _user_skill_names(db, user), payload.extracted_skills)

    job = SavedJob(
        user_id=user.id,
        source_url=payload.source_url,
        source_site=payload.source_site,
        import_method=payload.import_method,
        title=payload.title or "Untitled Role",
        company_name=payload.company_name,
        company_url=payload.company_url,
        location=payload.location,
        employment_type=payload.employment_type,
        is_remote=payload.is_remote,
        salary_min=payload.salary_min,
        salary_max=payload.salary_max,
        salary_currency=payload.salary_currency,
        description_raw=payload.description_raw,
        responsibilities=payload.responsibilities,
        requirements=payload.requirements,
        benefits=payload.benefits,
        extracted_skills=payload.extracted_skills,
        company_profile=payload.company_profile,
        verification_status=payload.verification_status,
        verification_sources=payload.verification_sources,
        match_score=match_score,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.get("/", response_model=list[SavedJobRead])
async def list_saved_jobs(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SavedJob]:
    """All jobs the current user has saved, most recently created first."""
    result = await db.execute(
        select(SavedJob).where(SavedJob.user_id == user.id).order_by(SavedJob.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/search", response_model=list[SavedJobRead])
async def search_saved_jobs(
    q: str | None = Query(default=None, description="Free-text match on title, company, or description"),
    location: str | None = Query(default=None),
    employment_type: str | None = Query(default=None),
    remote: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SavedJob]:
    """
    Search and filter the current user's OWN saved jobs.

    CareerKundi imports jobs by URL/paste rather than crawling external job
    boards, so there is no global job index to query — this endpoint searches
    what the user has already saved. `q` matches title / company / description;
    the remaining parameters filter by structured fields. Results are
    newest-first and paginated.

    NOTE: this route is declared BEFORE `/{job_id}` on purpose — FastAPI matches
    routes top-to-bottom, so if `/{job_id}` came first it would swallow the
    literal path "search" and try to parse it as a job UUID.
    """
    stmt = select(SavedJob).where(SavedJob.user_id == user.id)

    if q and q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                SavedJob.title.ilike(like),
                SavedJob.company_name.ilike(like),
                SavedJob.description_raw.ilike(like),
            )
        )
    if location and location.strip():
        stmt = stmt.where(SavedJob.location.ilike(f"%{location.strip()}%"))
    if employment_type:
        stmt = stmt.where(SavedJob.employment_type == employment_type)
    if remote is not None:
        stmt = stmt.where(SavedJob.is_remote.is_(remote))

    stmt = stmt.order_by(SavedJob.created_at.desc()).limit(page_size).offset((page - 1) * page_size)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{job_id}", response_model=SavedJobRead)
async def get_saved_job(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SavedJob:
    return await _get_owned_job(db, user, job_id)


@router.delete("/{job_id}", status_code=204)
async def delete_saved_job(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    job = await _get_owned_job(db, user, job_id)
    await db.delete(job)
    await db.commit()
    return Response(status_code=204)


@router.patch("/{job_id}/status", response_model=SavedJobRead)
async def update_job_status(
    job_id: uuid.UUID,
    payload: JobStatusUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SavedJob:
    """
    Update a saved job's application-tracking status (saved -> applied ->
    interviewing -> offered -> rejected). Powers the application tracker on
    the Job Search / Dashboard screens.
    """
    job = await _get_owned_job(db, user, job_id)
    job.status = payload.status
    await db.commit()
    await db.refresh(job)
    return job


@router.post("/{job_id}/interview-pack", response_model=InterviewPackRead)
async def generate_interview_pack(
    job_id: uuid.UUID,
    payload: InterviewPackRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InterviewPackRead:
    """
    Generate (or regenerate, e.g. with different `focus_areas`/`difficulty`)
    an interview pack for an already-saved, enriched job. The pack is
    persisted back onto the `SavedJob` row so `GET .../interview-pack` can
    serve it without re-running the pipeline.
    """
    job = await _get_owned_job(db, user, job_id)

    job_snapshot = {
        "title": job.title,
        "company_name": job.company_name,
        "description_raw": job.description_raw,
        "responsibilities": job.responsibilities,
        "requirements": job.requirements,
        "extracted_skills": job.extracted_skills,
    }

    result = await run_interview_pack_pipeline(
        user_id=str(user.id),
        job_snapshot=job_snapshot,
        focus_areas=payload.focus_areas,
        difficulty=payload.difficulty,
    )
    final_state = result["state"]
    cost_monitor = result["cost_monitor"]
    draft = final_state.get("draft_output") or {}
    questions = draft.get("questions", [])
    generated_at = datetime.now(timezone.utc)

    job.interview_pack = questions
    job.interview_pack_confidence = final_state.get("confidence_score")
    job.interview_pack_generated_at = generated_at
    await db.commit()

    await cost_monitor.persist(db, user_id=str(user.id), model_used=final_state.get("model_tier_used", "unknown"))
    await db.commit()  # CostMonitor.persist() only flushes — commit explicitly so the usage record survives session close

    return InterviewPackRead(
        job_id=str(job.id),
        questions=questions,
        confidence_score=job.interview_pack_confidence,
        generated_at=generated_at,
    )


@router.get("/{job_id}/interview-pack", response_model=InterviewPackRead)
async def get_interview_pack(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InterviewPackRead:
    job = await _get_owned_job(db, user, job_id)
    if not job.interview_pack:
        raise NotFoundError("No interview pack has been generated for this job yet.")
    return InterviewPackRead(
        job_id=str(job.id),
        questions=job.interview_pack,
        confidence_score=job.interview_pack_confidence,
        generated_at=job.interview_pack_generated_at,
    )
