"""
Private attachment scan queue skeleton (0053-F16).

Internal service helpers only — no scanner engine, no HTTP routes, no UI.
A queued scan job is not a completed scan and is not verification.
Does not mutate EvidenceRecord, ClaimRecord, or ReviewRequest.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.attachment_scan import AttachmentScanJob
from app.db.models.claim import ClaimRecord
from app.db.models.evidence import ClaimEvidenceLink, EvidenceRecord
from app.platform.evidence.attachment_safety import AttachmentSafetyStatus
from app.platform.evidence.refs import EvidenceRefError
from app.platform.evidence.service import get_evidence_for_owner

ACTIVE_SCAN_JOB_STATUSES: frozenset[str] = frozenset({"queued", "reserved"})

MSG_ATTACHMENT_REQUIRED = (
    "A private attachment is required before creating a scan job."
)
MSG_DUPLICATE_ACTIVE = (
    "An active scan job already exists for this attachment."
)
MSG_CANCEL_NOT_ACTIVE = "Only queued or reserved scan jobs can be cancelled."


class AttachmentScanJobStatus(StrEnum):
    QUEUED = "queued"
    RESERVED = "reserved"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


def attachment_scan_job_status_label(status: AttachmentScanJobStatus | str) -> str:
    value = (
        status.value
        if isinstance(status, AttachmentScanJobStatus)
        else str(status)
    )
    labels = {
        "queued": "Queued",
        "reserved": "Reserved",
        "completed": "Completed",
        "failed": "Failed",
        "cancelled": "Cancelled",
    }
    return labels.get(value, value)


async def _linked_claim_status_snapshot(
    db: AsyncSession, evidence_id: uuid.UUID
) -> list[tuple[uuid.UUID, str, str]]:
    rows = (
        await db.execute(
            select(
                ClaimRecord.id,
                ClaimRecord.support_status,
                ClaimRecord.verification_status,
            )
            .join(
                ClaimEvidenceLink,
                ClaimEvidenceLink.claim_id == ClaimRecord.id,
            )
            .where(ClaimEvidenceLink.evidence_id == evidence_id)
            .order_by(ClaimRecord.id)
        )
    ).all()
    return [(r[0], r[1], r[2]) for r in rows]


async def _get_active_job_for_hash(
    db: AsyncSession,
    *,
    evidence_id: uuid.UUID,
    content_hash: str,
) -> AttachmentScanJob | None:
    return (
        await db.execute(
            select(AttachmentScanJob).where(
                AttachmentScanJob.evidence_id == evidence_id,
                AttachmentScanJob.content_hash_snapshot == content_hash,
                AttachmentScanJob.job_status.in_(tuple(ACTIVE_SCAN_JOB_STATUSES)),
            )
        )
    ).scalar_one_or_none()


async def create_attachment_scan_job(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
    evidence_id: uuid.UUID,
) -> AttachmentScanJob:
    """
    Enqueue an internal scan job for an owned evidence attachment.

    Snapshots hash/mime/size only. Does not read file bytes, run a scanner,
    or mutate evidence/claim/review rows.
    """
    evidence = await get_evidence_for_owner(db, evidence_id, owner_user_id)
    if evidence is None:
        raise EvidenceRefError(f"evidence does not exist: {evidence_id}")

    if not evidence.storage_uri or not evidence.content_hash:
        raise EvidenceRefError(MSG_ATTACHMENT_REQUIRED)

    prior_claims = await _linked_claim_status_snapshot(db, evidence_id)
    prior_uri = evidence.storage_uri
    prior_hash = evidence.content_hash
    prior_mime = evidence.mime_type
    prior_size = evidence.size_bytes

    existing = await _get_active_job_for_hash(
        db,
        evidence_id=evidence_id,
        content_hash=evidence.content_hash,
    )
    if existing is not None:
        raise EvidenceRefError(MSG_DUPLICATE_ACTIVE)

    job = AttachmentScanJob(
        owner_user_id=owner_user_id,
        evidence_id=evidence_id,
        content_hash_snapshot=evidence.content_hash,
        mime_type_snapshot=evidence.mime_type,
        size_bytes_snapshot=evidence.size_bytes,
        job_status=AttachmentScanJobStatus.QUEUED.value,
        attachment_safety_status=AttachmentSafetyStatus.SCAN_PENDING.value,
        engine_name=None,
        engine_version=None,
        attempt_count=0,
        safe_error_code=None,
        safe_error_message=None,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    await db.refresh(evidence)
    if (
        evidence.storage_uri != prior_uri
        or evidence.content_hash != prior_hash
        or evidence.mime_type != prior_mime
        or evidence.size_bytes != prior_size
    ):
        raise EvidenceRefError(
            "create_attachment_scan_job must not mutate EvidenceRecord"
        )

    after_claims = await _linked_claim_status_snapshot(db, evidence_id)
    if after_claims != prior_claims:
        raise EvidenceRefError(
            "create_attachment_scan_job must not mutate claim support or "
            "verification status"
        )
    return job


async def get_attachment_scan_job_for_owner(
    db: AsyncSession,
    *,
    job_id: uuid.UUID,
    owner_user_id: uuid.UUID,
) -> AttachmentScanJob | None:
    job = (
        await db.execute(
            select(AttachmentScanJob).where(AttachmentScanJob.id == job_id)
        )
    ).scalar_one_or_none()
    if job is None or job.owner_user_id != owner_user_id:
        return None
    return job


async def list_attachment_scan_jobs_for_owner(
    db: AsyncSession,
    *,
    owner_user_id: uuid.UUID,
) -> list[AttachmentScanJob]:
    rows = (
        await db.execute(
            select(AttachmentScanJob)
            .where(AttachmentScanJob.owner_user_id == owner_user_id)
            .order_by(AttachmentScanJob.created_at.desc())
        )
    ).scalars().all()
    return list(rows)


async def get_latest_attachment_scan_job_for_evidence(
    db: AsyncSession,
    *,
    evidence_id: uuid.UUID,
    owner_user_id: uuid.UUID,
) -> AttachmentScanJob | None:
    evidence = await get_evidence_for_owner(db, evidence_id, owner_user_id)
    if evidence is None:
        return None
    return (
        await db.execute(
            select(AttachmentScanJob)
            .where(
                AttachmentScanJob.evidence_id == evidence_id,
                AttachmentScanJob.owner_user_id == owner_user_id,
            )
            .order_by(AttachmentScanJob.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


async def cancel_attachment_scan_job(
    db: AsyncSession,
    *,
    job_id: uuid.UUID,
    owner_user_id: uuid.UUID,
    reason: str | None = None,
) -> AttachmentScanJob:
    """Cancel an active (queued/reserved) job owned by the user."""
    job = await get_attachment_scan_job_for_owner(
        db, job_id=job_id, owner_user_id=owner_user_id
    )
    if job is None:
        raise EvidenceRefError(f"scan job does not exist: {job_id}")
    if job.job_status not in ACTIVE_SCAN_JOB_STATUSES:
        raise EvidenceRefError(MSG_CANCEL_NOT_ACTIVE)

    job.job_status = AttachmentScanJobStatus.CANCELLED.value
    job.cancelled_at = datetime.now(timezone.utc)
    if reason is not None:
        trimmed = reason.strip()
        job.safe_error_code = "cancelled"
        job.safe_error_message = trimmed[:500] if trimmed else None
    await db.commit()
    await db.refresh(job)
    return job
