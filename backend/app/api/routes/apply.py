"""
api/routes/apply.py
=====================
Job URL import and auto-apply endpoints.

POST  /apply/extract-url                  Import a job from a pasted URL
POST  /apply/jobs/{job_id}/apply          Start an auto-apply workflow
GET   /apply/jobs/{job_id}/applications   List applications for a job
GET   /apply/applications                 List all user's applications
PATCH /apply/applications/{app_id}/confirm    Explicit user confirmation gate
POST  /apply/applications/{app_id}/mark-manual-success  User marks manual as done

Safety architecture
-------------------
- The PATCH /confirm endpoint is the ONLY place `user_confirmed` is set True.
- The auto-apply pipeline refuses to proceed without it.
- `submitted_data` logs what was sent; passwords are never stored.
- All failure paths return `manual_apply_url` so the user can always finish manually.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.auto_apply import run_auto_apply_pipeline
from app.agents.job_extractor import run_job_extraction_pipeline
from app.api.deps import get_current_user
from app.core.errors import NotFoundError
from app.db.models.apply import JobApplication
from app.db.models.job import SavedJob
from app.db.models.user import User
from app.db.session import get_db
from app.services.badges import fire_event

router = APIRouter(prefix="/apply", tags=["apply"])


# ---------------------------------------------------------------------------
# Schemas (inline — small enough not to need a separate schemas file)
# ---------------------------------------------------------------------------

class ExtractURLRequest(BaseModel):
    url: str


class ExtractURLResponse(BaseModel):
    extracted_fields: dict
    extraction_incomplete: bool
    missing_fields: list[str]
    guardrail_passed: bool
    guardrail_issues: list[str]
    blocked_domain: bool = False


class StartApplyRequest(BaseModel):
    cv_id: uuid.UUID | None = None
    cover_letter_requested: bool = False
    # NOTE: user_confirmed is intentionally NOT here —
    # it must come through the separate /confirm endpoint.


class ApplicationRead(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    cv_id: uuid.UUID | None
    status: str
    status_detail: str | None
    cover_letter_text: str | None
    manual_apply_url: str | None
    platform_confirmation: str | None
    tracker_log: list
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConfirmApplyResponse(BaseModel):
    application_id: uuid.UUID
    status: str
    status_detail: str | None
    platform_confirmation: str | None
    manual_apply_url: str | None
    tracker_log: list
    newly_earned_badges: list[str] = []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_owned_job(db: AsyncSession, user: User, job_id: uuid.UUID) -> SavedJob:
    result = await db.execute(
        select(SavedJob).where(SavedJob.id == job_id, SavedJob.user_id == user.id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise NotFoundError("Saved job not found.")
    return job


async def _get_owned_application(
    db: AsyncSession, user: User, app_id: uuid.UUID
) -> JobApplication:
    result = await db.execute(
        select(JobApplication).where(
            JobApplication.id == app_id,
            JobApplication.user_id == user.id,
        )
    )
    app = result.scalar_one_or_none()
    if app is None:
        raise NotFoundError("Application not found.")
    return app


def _job_to_dict(job: SavedJob) -> dict:
    return {
        "title": job.title,
        "company_name": job.company_name,
        "location": job.location,
        "description_raw": job.description_raw,
        "source_url": job.source_url,
        "responsibilities": job.responsibilities,
        "requirements": job.requirements,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/extract-url", response_model=ExtractURLResponse, status_code=200)
async def extract_job_from_url(
    payload: ExtractURLRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExtractURLResponse:
    """
    Scrape and extract structured job fields from a posted URL.

    If the domain is blocked or scraping fails, returns `extraction_incomplete=True`
    with whatever partial data we could extract, plus the list of `missing_fields`
    so the UI can render editable form fields for the user to fill manually.
    """
    result = await run_job_extraction_pipeline(
        user_id=str(user.id),
        job_url=payload.url,
    )
    state = result["state"]
    cost_monitor = result["cost_monitor"]

    await cost_monitor.persist(db)
    await db.commit()

    # Fire badge for first URL import
    await fire_event(db, user.id, "job_url_imported")
    await db.commit()

    blocked = (
        not state.get("guardrail_passed")
        and any("block" in i.lower() for i in state.get("guardrail_issues", []))
    )

    return ExtractURLResponse(
        extracted_fields=state.get("extracted_fields", {}),
        extraction_incomplete=state.get("extraction_incomplete", True),
        missing_fields=state.get("missing_fields", []),
        guardrail_passed=state.get("guardrail_passed", False),
        guardrail_issues=state.get("guardrail_issues", []),
        blocked_domain=blocked,
    )


@router.post("/jobs/{job_id}/apply", response_model=ApplicationRead, status_code=201)
async def start_apply_workflow(
    job_id: uuid.UUID,
    payload: StartApplyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApplicationRead:
    """
    Create a JobApplication record in `draft` state.

    The pipeline will not submit anything yet — that requires the user to
    call PATCH /apply/applications/{app_id}/confirm explicitly.
    """
    job = await _get_owned_job(db, user, job_id)

    # Create the draft application record
    app = JobApplication(
        user_id=user.id,
        job_id=job.id,
        cv_id=payload.cv_id,
        user_confirmed=False,
        status="awaiting_confirmation",
        status_detail="Waiting for your explicit confirmation before submitting.",
        cover_letter_requested=payload.cover_letter_requested,
        manual_apply_url=job.source_url,
    )
    db.add(app)
    await db.flush()

    # Pre-generate cover letter if requested
    if payload.cover_letter_requested:
        cl_result = await run_auto_apply_pipeline(
            user_id=str(user.id),
            job_data=_job_to_dict(job),
            profile_data={},
            cv_id=str(payload.cv_id) if payload.cv_id else None,
            user_confirmed=False,
            cover_letter_requested=True,
            profile_sufficient=False,
        )
        cl_state = cl_result["state"]
        app.cover_letter_text = cl_state.get("cover_letter_text")
        app.cover_letter_generated = bool(app.cover_letter_text)

    await db.commit()
    await db.refresh(app)
    return ApplicationRead.model_validate(app)


@router.patch("/applications/{app_id}/confirm", response_model=ConfirmApplyResponse)
async def confirm_and_submit(
    app_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConfirmApplyResponse:
    """
    **Explicit user confirmation gate.**

    The user presses "Confirm & Submit" in the UI. Only then do we set
    `user_confirmed=True` and run the full submission pipeline.

    This is the ONLY endpoint that sets user_confirmed=True.
    """
    app = await _get_owned_application(db, user, app_id)
    job = await _get_owned_job(db, user, app.job_id)

    if app.user_confirmed:
        raise HTTPException(
            status_code=409,
            detail="This application has already been confirmed and submitted."
        )

    app.user_confirmed = True
    app.confirmed_at = datetime.now(timezone.utc)
    app.status = "submitting"
    await db.flush()

    # Determine profile completeness (simplified check)
    from app.db.models.profile import Profile
    profile_result = await db.execute(
        select(Profile).where(Profile.user_id == user.id)
    )
    profile = profile_result.scalar_one_or_none()
    profile_sufficient = bool(profile and profile.completeness_score and profile.completeness_score >= 60)

    profile_data = {}
    if profile:
        profile_data = {
            "full_name": user.full_name,
            "professional_headline": profile.professional_headline,
            "bio_summary": profile.bio_summary,
            "linkedin_url": profile.linkedin_url,
        }

    # Run the submission pipeline
    result = await run_auto_apply_pipeline(
        user_id=str(user.id),
        job_data=_job_to_dict(job),
        profile_data=profile_data,
        cv_id=str(app.cv_id) if app.cv_id else None,
        user_confirmed=True,
        cover_letter_requested=app.cover_letter_generated,
        profile_sufficient=profile_sufficient,
    )
    state = result["state"]
    cost_monitor = result["cost_monitor"]

    # Persist result to the application record
    final_status = state.get("final_status") or state.get("apply_status", "unknown")
    app.status = final_status
    app.status_detail = state.get("status_detail")
    app.platform_confirmation = state.get("platform_confirmation")
    app.manual_apply_url = state.get("manual_apply_url") or job.source_url
    app.tracker_log = state.get("tracker_log", [])
    if state.get("cover_letter_text"):
        app.cover_letter_text = state["cover_letter_text"]
    if final_status == "submitted":
        app.submitted_at = datetime.now(timezone.utc)
    if state.get("failure_reason"):
        app.failure_reason = state["failure_reason"]

    await db.commit()
    await cost_monitor.persist(db)
    await db.commit()

    # Badge events
    newly_earned: list[str] = []
    if final_status == "submitted":
        newly_earned += await fire_event(db, user.id, "job_applied")
        await db.commit()

    return ConfirmApplyResponse(
        application_id=app.id,
        status=app.status,
        status_detail=app.status_detail,
        platform_confirmation=app.platform_confirmation,
        manual_apply_url=app.manual_apply_url,
        tracker_log=app.tracker_log,
        newly_earned_badges=newly_earned,
    )


@router.get("/applications", response_model=list[ApplicationRead])
async def list_applications(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ApplicationRead]:
    result = await db.execute(
        select(JobApplication)
        .where(JobApplication.user_id == user.id)
        .order_by(JobApplication.created_at.desc())
    )
    apps = result.scalars().all()
    return [ApplicationRead.model_validate(a) for a in apps]


@router.get("/jobs/{job_id}/applications", response_model=list[ApplicationRead])
async def list_job_applications(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ApplicationRead]:
    await _get_owned_job(db, user, job_id)  # ownership check
    result = await db.execute(
        select(JobApplication)
        .where(JobApplication.job_id == job_id, JobApplication.user_id == user.id)
        .order_by(JobApplication.created_at.desc())
    )
    apps = result.scalars().all()
    return [ApplicationRead.model_validate(a) for a in apps]
