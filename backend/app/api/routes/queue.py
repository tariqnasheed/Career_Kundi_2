"""
api/routes/queue.py
=====================
Background job queue for heavy generation tasks.

POST  /queue/jobs                   Enqueue a new generation job
GET   /queue/jobs                   List user's jobs (with status)
GET   /queue/jobs/{job_id}          Poll a specific job
DELETE /queue/jobs/{job_id}         Cancel a pending job

Architecture
------------
Jobs are persisted to the `generation_jobs` table immediately (status=pending).
An `asyncio.create_task` then runs the actual work in the background so the
HTTP response returns instantly with the job record.

Supported job_type values and their input_params:
  interview_pack_pdf  → {saved_job_id: UUID}
  roadmap_pdf         → {roadmap_id: UUID}
  cv_export           → {cv_id: UUID, template: str | None}
  study_bundle        → {roadmap_id: UUID, milestone_ids: list[str]}
  practice_bank       → {target_role: str, skill_ids: list[str]}
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.errors import NotFoundError
from app.db.models.queue import GenerationJob
from app.db.models.user import User
from app.db.session import get_db, async_session_factory

router = APIRouter(prefix="/queue", tags=["queue"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class EnqueueRequest(BaseModel):
    job_type: str
    label: str = ""
    input_params: dict[str, Any] = {}


class JobRead(BaseModel):
    id: uuid.UUID
    job_type: str
    label: str
    status: str
    progress: int
    current_step: str | None
    result_data: dict | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------

_VALID_JOB_TYPES = frozenset({
    "interview_pack_pdf", "roadmap_pdf", "cv_export",
    "study_bundle", "practice_bank",
})

async def _run_generation_job(job_id: uuid.UUID, user_id: uuid.UUID) -> None:
    """
    Background task that executes the generation work and updates the
    GenerationJob record with progress + result.

    Uses its own DB session (separate from the request session that has
    already returned its response).
    """
    async with async_session_factory() as db:
        job = await db.get(GenerationJob, job_id)
        if not job or job.status != "pending":
            return

        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        await db.commit()

        try:
            result = await _execute_job(job, db)
            job.status = "done"
            job.progress = 100
            job.result_data = result
            job.completed_at = datetime.now(timezone.utc)
            job.current_step = "Complete"
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)[:500]
            job.completed_at = datetime.now(timezone.utc)

        await db.commit()


async def _execute_job(job: GenerationJob, db: AsyncSession) -> dict[str, Any]:
    """Dispatch to the appropriate generation pipeline."""

    async def _update_progress(step: str, pct: int) -> None:
        job.current_step = step
        job.progress = pct
        await db.commit()

    params = job.input_params

    if job.job_type == "interview_pack_pdf":
        await _update_progress("Loading job data", 10)
        from app.db.models.job import SavedJob
        saved_job = await db.get(SavedJob, uuid.UUID(params["saved_job_id"]))
        if not saved_job:
            raise ValueError("Job not found")
        await _update_progress("Generating interview pack content", 40)
        await asyncio.sleep(0.5)  # mock: simulate generation time
        await _update_progress("Formatting PDF", 80)
        await asyncio.sleep(0.2)
        return {
            "download_url": f"/downloads/interview-pack-{job.id}.pdf",
            "file_size_kb": 248,
            "pages": 12,
            "job_title": saved_job.title,
        }

    elif job.job_type == "roadmap_pdf":
        await _update_progress("Loading roadmap", 10)
        from app.db.models.roadmap import Roadmap
        roadmap = await db.get(Roadmap, uuid.UUID(params["roadmap_id"]))
        if not roadmap:
            raise ValueError("Roadmap not found")
        await _update_progress("Generating content sections", 50)
        await asyncio.sleep(0.5)
        await _update_progress("Formatting PDF", 85)
        await asyncio.sleep(0.2)
        return {
            "download_url": f"/downloads/roadmap-{job.id}.pdf",
            "file_size_kb": 184,
            "pages": 8,
            "target_role": roadmap.target_role,
        }

    elif job.job_type == "cv_export":
        await _update_progress("Loading CV", 10)
        from app.db.models.cv import GeneratedCV
        cv = await db.get(GeneratedCV, uuid.UUID(params["cv_id"]))
        if not cv:
            raise ValueError("CV not found")
        template = params.get("template", cv.template_name or "modern")
        await _update_progress(f"Rendering {template} template", 45)
        await asyncio.sleep(0.4)
        await _update_progress("Exporting PDF + DOCX", 80)
        await asyncio.sleep(0.2)
        return {
            "download_url": f"/downloads/cv-{job.id}.pdf",
            "docx_url": f"/downloads/cv-{job.id}.docx",
            "file_size_kb": 96,
            "template": template,
        }

    elif job.job_type == "study_bundle":
        await _update_progress("Generating study materials", 30)
        await asyncio.sleep(0.8)
        await _update_progress("Packaging bundle", 85)
        await asyncio.sleep(0.2)
        return {
            "download_url": f"/downloads/study-bundle-{job.id}.zip",
            "file_size_kb": 512,
            "module_count": 5,
        }

    elif job.job_type == "practice_bank":
        target_role = params.get("target_role", "Software Engineer")
        await _update_progress(f"Generating question bank for {target_role}", 40)
        await asyncio.sleep(0.6)
        await _update_progress("Formatting questions", 80)
        await asyncio.sleep(0.2)
        return {
            "download_url": f"/downloads/practice-bank-{job.id}.pdf",
            "question_count": 120,
            "target_role": target_role,
        }

    else:
        raise ValueError(f"Unknown job_type: {job.job_type}")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/jobs", response_model=JobRead, status_code=202)
async def enqueue_job(
    payload: EnqueueRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobRead:
    """Enqueue a generation job. Returns immediately with status=pending."""
    if payload.job_type not in _VALID_JOB_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"job_type must be one of: {sorted(_VALID_JOB_TYPES)}"
        )

    job = GenerationJob(
        user_id=user.id,
        job_type=payload.job_type,
        label=payload.label or payload.job_type.replace("_", " ").title(),
        input_params=payload.input_params,
        status="pending",
        progress=0,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Fire background task — does NOT block the response
    asyncio.create_task(_run_generation_job(job.id, user.id))

    return JobRead.model_validate(job)


@router.get("/jobs", response_model=list[JobRead])
async def list_queue(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[JobRead]:
    result = await db.execute(
        select(GenerationJob)
        .where(GenerationJob.user_id == user.id)
        .order_by(GenerationJob.created_at.desc())
        .limit(50)
    )
    return [JobRead.model_validate(j) for j in result.scalars()]


@router.get("/jobs/{job_id}", response_model=JobRead)
async def get_job(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobRead:
    result = await db.execute(
        select(GenerationJob).where(
            GenerationJob.id == job_id,
            GenerationJob.user_id == user.id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundError("Generation job not found.")
    return JobRead.model_validate(job)


@router.delete("/jobs/{job_id}", status_code=204)
async def cancel_job(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(GenerationJob).where(
            GenerationJob.id == job_id,
            GenerationJob.user_id == user.id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundError("Generation job not found.")
    if job.status not in ("pending", "running"):
        raise HTTPException(status_code=409, detail=f"Cannot cancel a job with status='{job.status}'.")
    job.status = "cancelled"
    await db.commit()
