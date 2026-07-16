"""Attachment scan queue skeleton service tests (0053-F16)."""

from __future__ import annotations

import ast
import asyncio
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.db.migration_runner import foundation_heads, prepare_database
from app.db.models.attachment_scan import AttachmentScanJob
from app.db.models.career_subject import CareerSubject
from app.db.models.claim import ClaimRecord
from app.db.models.evidence import ClaimEvidenceLink, EvidenceRecord
from app.db.models.review_request import ReviewRequest
from app.db.models.user import SubscriptionPlan, User, UserRole
from app.db.tests.pf1_test_db import require_disposable_postgres, temporary_database
from app.main import app
from app.platform.claims import ClaimKind, ClaimOrigin, SupportStatus, VerificationStatus
from app.platform.claims.service import create_claim
from app.platform.evidence import (
    ClaimEvidenceLinkRole,
    EvidenceKind,
    EvidencePrivacyClass,
    EvidenceRefError,
)
from app.platform.evidence.attachment_safety import (
    AttachmentSafetyStatus,
    current_attachment_safety_status,
)
from app.platform.evidence.attachment_scan_queue import (
    AttachmentScanJobStatus,
    cancel_attachment_scan_job,
    create_attachment_scan_job,
    get_attachment_scan_job_for_owner,
    get_latest_attachment_scan_job_for_evidence,
    list_attachment_scan_jobs_for_owner,
)
from app.platform.evidence.service import (
    create_evidence_record,
    link_evidence_to_claim,
)
from app.platform.identity.refs import ActorRef, ActorType
from app.platform.kernel import new_entity_id
from app.platform.verification.service import create_review_request
from app.platform.verification.status import ReviewState

F16_PREFIX = "ck_f2svc_"
F0011 = "f0011_attachment_scan_queue"
QUEUE_MODULE = (
    Path(__file__).resolve().parents[1] / "attachment_scan_queue.py"
)
REPO_ROOT = Path(__file__).resolve().parents[5]


def _async_url(sync_url: str) -> str:
    return sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)


def _insert_user(sync_url: str, *, email_prefix: str = "f16") -> uuid.UUID:
    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)
    uid = uuid.uuid4()
    try:
        with Session() as session:
            session.add(
                User(
                    id=uid,
                    email=f"{email_prefix}-{uid.hex[:8]}@example.com",
                    hashed_password=hash_password("test-password-ok"),
                    full_name="F16 User",
                    role=UserRole.USER,
                    plan=SubscriptionPlan.FREE,
                    is_active=True,
                    is_email_verified=False,
                )
            )
            session.commit()
    finally:
        engine.dispose()
    return uid


def test_migration_head_is_f0011() -> None:
    assert foundation_heads() == [F0011]


def test_no_scan_routes_in_openapi() -> None:
    paths = set(app.openapi().get("paths", {}))
    assert "/api/v1/evidence/{evidence_id}/scan" not in paths
    assert "/api/v1/evidence/{evidence_id}/rescan" not in paths
    assert "/api/v1/evidence/scan-jobs" not in paths
    for path in paths:
        if not path.startswith("/api/v1/evidence"):
            continue
        assert "/scan" not in path.lower(), path


def test_queue_module_has_no_scanner_ocr_llm_imports() -> None:
    source = QUEUE_MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
    blob = source.lower()
    for forbidden in (
        "clamav",
        "virustotal",
        "pytesseract",
        "pdfplumber",
        "easyocr",
        "openai",
        "anthropic",
        "app.tools.llm",
    ):
        assert forbidden not in blob
        assert not any(forbidden in mod for mod in imports)
    for phrase in (
        "safe file",
        "clean file",
        "trusted file",
        "verified document",
    ):
        assert phrase not in blob


def test_frontend_has_no_scan_button() -> None:
    pages = [
        REPO_ROOT / "frontend" / "src" / "pages" / "EvidenceLibraryPage.tsx",
        REPO_ROOT
        / "frontend"
        / "src"
        / "features"
        / "passport"
        / "PassportEvidencePanel.tsx",
    ]
    for path in pages:
        text = path.read_text(encoding="utf-8").lower()
        assert "scan attachment" not in text
        assert "run malware scan" not in text
        assert "rescan" not in text
        assert 'name: "scan"' not in text


def test_public_safety_status_still_scan_not_available() -> None:
    assert (
        current_attachment_safety_status()
        is AttachmentSafetyStatus.SCAN_NOT_AVAILABLE
    )


@require_disposable_postgres
def test_attachment_scan_queue_service_guards() -> None:
    with temporary_database(prefix=F16_PREFIX) as (_name, url):
        prepare_database(url)
        assert foundation_heads() == [F0011]
        user_a = _insert_user(url, email_prefix="f16a")
        user_b = _insert_user(url, email_prefix="f16b")

        async def _run() -> None:
            engine = create_async_engine(_async_url(url), pool_pre_ping=True)
            sessions = async_sessionmaker(
                bind=engine, expire_on_commit=False, class_=AsyncSession
            )
            try:
                async with sessions() as db:
                    subject = CareerSubject(owner_user_id=user_a)
                    db.add(subject)
                    await db.commit()
                    await db.refresh(subject)

                    actor = ActorRef(
                        actor_type=ActorType.USER, actor_id=new_entity_id()
                    )
                    bare = await create_evidence_record(
                        db,
                        owner_user_id=user_a,
                        subject_id=subject.id,
                        title="Bare metadata",
                        evidence_kind=EvidenceKind.DOCUMENT,
                        privacy_class=EvidencePrivacyClass.PRIVATE,
                        created_by_actor=actor,
                    )
                    with pytest.raises(
                        EvidenceRefError, match="private attachment is required"
                    ):
                        await create_attachment_scan_job(
                            db,
                            owner_user_id=user_a,
                            evidence_id=bare.id,
                        )

                    attached = await create_evidence_record(
                        db,
                        owner_user_id=user_a,
                        subject_id=subject.id,
                        title="Attached evidence",
                        evidence_kind=EvidenceKind.DOCUMENT,
                        privacy_class=EvidencePrivacyClass.PRIVATE,
                        storage_uri=(
                            f"local-evidence://{user_a}/{uuid.uuid4()}/note.txt"
                        ),
                        content_hash="a" * 64,
                        mime_type="text/plain",
                        size_bytes=12,
                        created_by_actor=actor,
                    )
                    claim = await create_claim(
                        db,
                        subject_id=subject.id,
                        claim_kind=ClaimKind.SKILL,
                        claim_key="python",
                        claim_value="Python",
                        claim_origin=ClaimOrigin.USER_ASSERTED,
                        support_status=SupportStatus.NOT_PROVIDED,
                        verification_status=VerificationStatus.UNVERIFIED,
                        created_by_actor=actor,
                    )
                    await link_evidence_to_claim(
                        db,
                        claim_id=claim.id,
                        evidence_id=attached.id,
                        link_role=ClaimEvidenceLinkRole.SUPPORTS,
                        created_by_actor=actor,
                    )
                    review = await create_review_request(
                        db,
                        owner_user_id=user_a,
                        claim_id=claim.id,
                        created_by_actor=actor,
                    )
                    prior_support = claim.support_status
                    prior_verification = claim.verification_status
                    prior_review_state = review.review_state
                    prior_hash = attached.content_hash
                    prior_uri = attached.storage_uri

                    # Other user cannot enqueue
                    with pytest.raises(EvidenceRefError, match="does not exist"):
                        await create_attachment_scan_job(
                            db,
                            owner_user_id=user_b,
                            evidence_id=attached.id,
                        )

                    job = await create_attachment_scan_job(
                        db,
                        owner_user_id=user_a,
                        evidence_id=attached.id,
                    )
                    assert job.job_status == AttachmentScanJobStatus.QUEUED.value
                    assert (
                        job.attachment_safety_status
                        == AttachmentSafetyStatus.SCAN_PENDING.value
                    )
                    assert job.content_hash_snapshot == "a" * 64
                    assert job.mime_type_snapshot == "text/plain"
                    assert job.size_bytes_snapshot == 12
                    assert job.engine_name is None
                    assert job.owner_user_id == user_a

                    job_dict = {
                        c.name: getattr(job, c.name) for c in job.__table__.columns
                    }
                    blob = " ".join(str(v) for v in job_dict.values()).lower()
                    assert "/tmp/" not in blob
                    assert "evidence_files" not in blob
                    assert "public" not in blob or "not" in blob

                    with pytest.raises(EvidenceRefError, match="active scan job"):
                        await create_attachment_scan_job(
                            db,
                            owner_user_id=user_a,
                            evidence_id=attached.id,
                        )

                    listed_a = await list_attachment_scan_jobs_for_owner(
                        db, owner_user_id=user_a
                    )
                    listed_b = await list_attachment_scan_jobs_for_owner(
                        db, owner_user_id=user_b
                    )
                    assert len(listed_a) == 1
                    assert listed_b == []
                    assert (
                        await get_attachment_scan_job_for_owner(
                            db, job_id=job.id, owner_user_id=user_b
                        )
                        is None
                    )
                    latest = await get_latest_attachment_scan_job_for_evidence(
                        db,
                        evidence_id=attached.id,
                        owner_user_id=user_a,
                    )
                    assert latest is not None
                    assert latest.id == job.id

                    cancelled = await cancel_attachment_scan_job(
                        db,
                        job_id=job.id,
                        owner_user_id=user_a,
                        reason="user cancelled",
                    )
                    assert (
                        cancelled.job_status
                        == AttachmentScanJobStatus.CANCELLED.value
                    )

                    # Historical cancelled job does not block a new enqueue
                    job2 = await create_attachment_scan_job(
                        db,
                        owner_user_id=user_a,
                        evidence_id=attached.id,
                    )
                    assert job2.id != job.id
                    assert job2.job_status == AttachmentScanJobStatus.QUEUED.value

                    await db.refresh(attached)
                    await db.refresh(claim)
                    await db.refresh(review)
                    assert attached.content_hash == prior_hash
                    assert attached.storage_uri == prior_uri
                    assert claim.support_status == prior_support
                    assert claim.verification_status == prior_verification
                    assert review.review_state == prior_review_state
                    assert review.review_state == ReviewState.REQUESTED.value

                sync_engine = create_engine(url)
                try:
                    with sync_engine.connect() as conn:
                        assert (
                            conn.execute(
                                text(
                                    "SELECT COUNT(*) FROM attachment_scan_jobs "
                                    "WHERE evidence_id = :eid"
                                ),
                                {"eid": attached.id},
                            ).scalar_one()
                            == 2
                        )
                        assert (
                            conn.execute(
                                select(func.count())
                                .select_from(EvidenceRecord)
                                .where(EvidenceRecord.id == attached.id)
                            ).scalar_one()
                            == 1
                        )
                        assert (
                            conn.execute(
                                select(func.count())
                                .select_from(ClaimEvidenceLink)
                                .where(ClaimEvidenceLink.evidence_id == attached.id)
                            ).scalar_one()
                            == 1
                        )
                        assert (
                            conn.execute(
                                select(func.count())
                                .select_from(ReviewRequest)
                                .where(ReviewRequest.claim_id == claim.id)
                            ).scalar_one()
                            == 1
                        )
                        assert (
                            conn.execute(
                                select(func.count()).select_from(ClaimRecord)
                            ).scalar_one()
                            == 1
                        )
                finally:
                    sync_engine.dispose()
            finally:
                await engine.dispose()

        asyncio.run(_run())
