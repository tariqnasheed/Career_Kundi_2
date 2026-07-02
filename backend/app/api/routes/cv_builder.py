"""
api/routes/cv_builder.py
=============================
CV Builder & ATS Optimization (§4.3) endpoints.

Thin HTTP wrapper around `app.agents.cv_builder.graph`'s two pipelines plus
the deterministic, non-generative `render.py::render_cv()` step and
`tools/document_export.py`'s exporters. No agent logic, prompting, RAG, or
verification happens in this file — see `app/agents/cv_builder/` for all of
that.

Endpoint summary
----------------
POST   /api/v1/cv-builder/generate              — Generate a new CV from the user's profile.
GET    /api/v1/cv-builder/                      — List the current user's saved CVs.
GET    /api/v1/cv-builder/{cv_id}                — Fetch one saved CV.
DELETE /api/v1/cv-builder/{cv_id}                — Delete a saved CV.
POST   /api/v1/cv-builder/{cv_id}/regenerate     — Re-run the pipeline against an existing saved CV.
GET    /api/v1/cv-builder/{cv_id}/export         — Export a saved CV as PDF/DOCX/Markdown.
POST   /api/v1/cv-builder/improve-bullet         — Improve a single bullet ("Improve with AI").
"""

from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.cv_builder.graph import run_bullet_improvement_pipeline, run_cv_generation_pipeline
from app.agents.cv_builder.render import render_cv
from app.api.deps import get_current_user
from app.api.routes.profile import _get_or_create_profile
from app.core.errors import NotFoundError
from app.db.models.cv import GeneratedCV
from app.db.models.job import SavedJob
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.cv_builder import (
    BulletImprovementRequest,
    BulletImprovementResult,
    CVGenerateRequest,
    CVRead,
    CVRegenerateRequest,
)
from app.schemas.profile import ProfileRead
from app.tools.document_export import export_docx, export_markdown, export_pdf

router = APIRouter(prefix="/cv-builder", tags=["cv-builder"])

_EXPORT_CONTENT_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "markdown": "text/markdown",
}
_EXPORT_EXTENSIONS = {"pdf": "pdf", "docx": "docx", "markdown": "md"}


async def _get_owned_cv(db: AsyncSession, user: User, cv_id: uuid.UUID) -> GeneratedCV:
    """Fetch a `GeneratedCV` the current user actually owns, or raise `NotFoundError` (never leaks existence of other users' rows)."""
    result = await db.execute(select(GeneratedCV).where(GeneratedCV.id == cv_id, GeneratedCV.user_id == user.id))
    cv = result.scalar_one_or_none()
    if cv is None:
        raise NotFoundError("Generated CV not found.")
    return cv


async def _get_owned_target_job(db: AsyncSession, user: User, target_job_id: uuid.UUID | None) -> SavedJob | None:
    """Same ownership-checked-fetch pattern as `_get_owned_cv`, for the optional target job a CV can be tailored toward."""
    if target_job_id is None:
        return None
    result = await db.execute(select(SavedJob).where(SavedJob.id == target_job_id, SavedJob.user_id == user.id))
    job = result.scalar_one_or_none()
    if job is None:
        raise NotFoundError("Target job not found.")
    return job


def _profile_snapshot(profile, user: User) -> dict:
    """
    The CV pipeline (and `render.py`) only ever see a flat dict — never the
    ORM `Profile`/`User` rows directly. `full_name`/`email` live on `User`,
    not `Profile` (see app/db/models/user.py vs profile.py), so they're
    injected here after building the snapshot from `ProfileRead`.
    """
    snapshot = ProfileRead.model_validate(profile).model_dump(mode="json")
    snapshot["full_name"] = user.full_name
    snapshot["email"] = user.email
    return snapshot


def _target_job_snapshot(job: SavedJob | None) -> dict | None:
    if job is None:
        return None
    return {
        "title": job.title,
        "company_name": job.company_name,
        "description_raw": job.description_raw,
        "responsibilities": job.responsibilities,
        "requirements": job.requirements,
        "extracted_skills": job.extracted_skills,
    }


async def _generate_and_render(*, db: AsyncSession, user: User, payload: CVGenerateRequest):
    """
    Shared core of `generate_cv` and `regenerate_cv`: load the profile and
    optional target job, run the full Guardrail -> Planner -> Executor ->
    Reflector pipeline, then render the Reflector-approved draft into the
    `GeneratedCV.rendered_content` shape. Returns
    `(rendered_content, section_config, cost_monitor, final_state)` — the
    route handlers decide how to persist it (insert a new row vs. update an
    existing one in place).
    """
    profile = await _get_or_create_profile(db, user)
    target_job = await _get_owned_target_job(db, user, payload.target_job_id)

    profile_snapshot = _profile_snapshot(profile, user)
    target_job_snapshot = _target_job_snapshot(target_job)

    result = await run_cv_generation_pipeline(
        user_id=str(user.id),
        profile_snapshot=profile_snapshot,
        target_job_snapshot=target_job_snapshot,
        requested_section_ids=payload.section_ids,
        tone=payload.tone,
        generation_mode=payload.generation_mode,
        target_role_title=payload.target_role_title,
        target_role_description=payload.target_role_description,
    )
    final_state = result["state"]
    cost_monitor = result["cost_monitor"]
    draft = final_state.get("draft_output") or {}
    section_ids = (final_state.get("plan") or {}).get("section_ids", [])

    rendered_content = render_cv(
        profile=profile_snapshot,
        target_job=target_job_snapshot,
        draft={**draft, "target_role_title": payload.target_role_title},
        section_ids=section_ids,
        template=payload.template,
        tone=payload.tone,
        citations=final_state.get("citations", []),
        confidence_score=final_state.get("confidence_score", 0.0),
    )
    section_config = [{"section_id": section_id, "enabled": True} for section_id in section_ids]
    return rendered_content, section_config, cost_monitor, final_state


@router.post("/generate", response_model=CVRead, status_code=201)
async def generate_cv(
    payload: CVGenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GeneratedCV:
    """
    Run the full multi-agent pipeline against the user's profile (optionally
    tailored to a saved target job), render the approved draft, and persist
    it as a new `GeneratedCV` row.
    """
    rendered_content, section_config, cost_monitor, final_state = await _generate_and_render(
        db=db, user=user, payload=payload
    )

    cv = GeneratedCV(
        user_id=user.id,
        target_job_id=payload.target_job_id,
        name=payload.name or "Untitled CV",
        template=payload.template,
        section_config=section_config,
        rendered_content=rendered_content,
    )
    db.add(cv)
    await db.commit()
    await db.refresh(cv)

    await cost_monitor.persist(db, user_id=str(user.id), model_used=final_state.get("model_tier_used", "unknown"))
    await db.commit()  # CostMonitor.persist() only flushes — commit explicitly so the usage record survives session close

    return cv


@router.get("/", response_model=list[CVRead])
async def list_cvs(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[GeneratedCV]:
    """All CVs the current user has generated, most recently created first."""
    result = await db.execute(
        select(GeneratedCV).where(GeneratedCV.user_id == user.id).order_by(GeneratedCV.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{cv_id}", response_model=CVRead)
async def get_cv(
    cv_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GeneratedCV:
    return await _get_owned_cv(db, user, cv_id)


@router.delete("/{cv_id}", status_code=204)
async def delete_cv(
    cv_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    cv = await _get_owned_cv(db, user, cv_id)
    await db.delete(cv)
    await db.commit()
    return Response(status_code=204)


@router.post("/{cv_id}/regenerate", response_model=CVRead)
async def regenerate_cv(
    cv_id: uuid.UUID,
    payload: CVRegenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GeneratedCV:
    """Re-run the pipeline (e.g. after editing the profile, or to try a different template/tone) against an existing saved CV row, updating it in place rather than creating a new one."""
    cv = await _get_owned_cv(db, user, cv_id)

    rendered_content, section_config, cost_monitor, final_state = await _generate_and_render(
        db=db, user=user, payload=payload
    )

    cv.target_job_id = payload.target_job_id
    cv.name = payload.name or cv.name
    cv.template = payload.template
    cv.section_config = section_config
    cv.rendered_content = rendered_content
    await db.commit()
    await db.refresh(cv)

    await cost_monitor.persist(db, user_id=str(user.id), model_used=final_state.get("model_tier_used", "unknown"))
    await db.commit()  # CostMonitor.persist() only flushes — commit explicitly so the usage record survives session close

    return cv


@router.get("/{cv_id}/export")
async def export_cv(
    cv_id: uuid.UUID,
    format: Literal["pdf", "docx", "markdown"] = "pdf",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Export an already-generated CV as PDF, DOCX, or Markdown. Purely
    deterministic template rendering over the saved `rendered_content`
    snapshot (see `tools/document_export.py`) — no agent pipeline, no LLM
    call, and no additional cost involved no matter how many times a user
    re-exports the same CV in a different format.
    """
    cv = await _get_owned_cv(db, user, cv_id)

    if format == "pdf":
        content = export_pdf(cv.rendered_content, template=cv.template)
    elif format == "docx":
        content = export_docx(cv.rendered_content)
    else:
        content = export_markdown(cv.rendered_content)

    cv.export_format_last_used = format
    await db.commit()

    filename = f"{(cv.name or 'cv').strip().replace(' ', '_')}.{_EXPORT_EXTENSIONS[format]}"
    return Response(
        content=content,
        media_type=_EXPORT_CONTENT_TYPES[format],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/improve-bullet", response_model=BulletImprovementResult)
async def improve_bullet(
    payload: BulletImprovementRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BulletImprovementResult:
    """Single-bullet 'Improve with AI' — the lightweight pipeline used directly from the Profile page, independent of full CV generation."""
    target_job = await _get_owned_target_job(db, user, payload.target_job_id)

    result = await run_bullet_improvement_pipeline(
        user_id=str(user.id),
        bullet_text=payload.bullet_text,
        bullet_context={
            "role_title": payload.context_role_title,
            "company_name": payload.context_company_name,
            "section_type": payload.section_type,
        },
        target_job_snapshot=_target_job_snapshot(target_job),
    )
    final_state = result["state"]
    cost_monitor = result["cost_monitor"]
    draft = final_state.get("draft_output") or {}

    await cost_monitor.persist(db, user_id=str(user.id), model_used=final_state.get("model_tier_used", "unknown"))
    await db.commit()  # CostMonitor.persist() only flushes — commit explicitly so the usage record survives session close

    return BulletImprovementResult(
        original_bullet=draft.get("original_bullet", payload.bullet_text),
        improved_bullet=draft.get("improved_bullet", payload.bullet_text),
        rationale=draft.get("rationale", ""),
        citations=final_state.get("citations", []),
        confidence_score=final_state.get("confidence_score", 0.0),
    )
