"""AttachmentScanJob result persistence guard tests (0053-F22)."""

from __future__ import annotations

import ast
import asyncio
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.db.migration_runner import foundation_heads, prepare_database
from app.db.models.career_subject import CareerSubject
from app.db.models.user import SubscriptionPlan, User, UserRole
from app.db.tests.pf1_test_db import require_disposable_postgres, temporary_database
from app.main import app
from app.platform.claims import ClaimKind, ClaimOrigin, SupportStatus, VerificationStatus
from app.platform.claims.service import create_claim
from app.platform.evidence import (
    ClaimEvidenceLinkRole,
    EvidenceKind,
    EvidencePrivacyClass,
)
from app.platform.evidence.attachment_local_scanner_adapter import (
    DisabledLocalProcessScannerAdapter,
)
from app.platform.evidence.attachment_safety import AttachmentSafetyStatus
from app.platform.evidence.attachment_scan_queue import (
    AttachmentScanJobStatus,
    create_attachment_scan_job,
)
from app.platform.evidence.attachment_scan_result_persistence import (
    ScanJobPersistenceError,
    assert_scan_job_update_allowed,
    apply_scan_job_update_plan,
    build_persistable_scan_job_update_plan,
    normalize_scan_job_update_plan,
    persistence_guard_summary,
    plan_is_persistable,
)
from app.platform.evidence.attachment_scan_worker import (
    ScanWorkerAction,
    build_scan_job_update_from_result,
)
from app.platform.evidence.attachment_scanner_adapter import (
    NoopUnavailableScannerAdapter,
)
from app.platform.evidence.service import create_evidence_record, link_evidence_to_claim
from app.platform.identity.refs import ActorRef, ActorType
from app.platform.kernel import new_entity_id
from app.platform.verification.service import create_review_request

REPO_ROOT = Path(__file__).resolve().parents[5]
PERSIST = (
    REPO_ROOT
    / "backend"
    / "app"
    / "platform"
    / "evidence"
    / "attachment_scan_result_persistence.py"
)
EVIDENCE_PKG = REPO_ROOT / "backend" / "app" / "platform" / "evidence"
# Reuse approved disposable prefix from pf1_test_db (do not expand allowlist in F22).
F22_PREFIX = "ck_f2svc_"
F0011 = "f0011_attachment_scan_queue"
FRONTEND_PAGES = [
    REPO_ROOT / "frontend" / "src" / "pages" / "EvidenceLibraryPage.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "passport"
    / "PassportEvidencePanel.tsx",
]


def _job(status: str) -> SimpleNamespace:
    return SimpleNamespace(job_status=status)


def _async_url(sync_url: str) -> str:
    return sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)


def _insert_user(sync_url: str, *, email_prefix: str = "f22") -> uuid.UUID:
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
                    full_name="F22 User",
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


def test_allowed_transitions_and_rejects() -> None:
    reserve = build_persistable_scan_job_update_plan(
        action=ScanWorkerAction.RESERVE_JOB,
        job_status=AttachmentScanJobStatus.RESERVED.value,
        attachment_safety_status=AttachmentSafetyStatus.SCAN_PENDING.value,
    )
    assert_scan_job_update_allowed(_job("queued"), reserve)

    passed = build_persistable_scan_job_update_plan(
        action=ScanWorkerAction.COMPLETE_PASSED,
        job_status=AttachmentScanJobStatus.COMPLETED.value,
        attachment_safety_status=AttachmentSafetyStatus.SCAN_PASSED.value,
        engine_name="test-engine",
        engine_version="0",
    )
    assert_scan_job_update_allowed(_job("reserved"), passed)

    failed = build_persistable_scan_job_update_plan(
        action=ScanWorkerAction.COMPLETE_FAILED,
        job_status=AttachmentScanJobStatus.COMPLETED.value,
        attachment_safety_status=AttachmentSafetyStatus.SCAN_FAILED.value,
        safe_error_code="scanner_error",
        safe_error_message="concerning result",
    )
    assert_scan_job_update_allowed(_job("reserved"), failed)

    errored = build_persistable_scan_job_update_plan(
        action=ScanWorkerAction.MARK_ERROR,
        job_status=AttachmentScanJobStatus.FAILED.value,
        attachment_safety_status=AttachmentSafetyStatus.SCAN_ERROR.value,
        safe_error_code="scanner_timeout",
        safe_error_message="timed out",
    )
    assert_scan_job_update_allowed(_job("reserved"), errored)

    cancel_q = build_persistable_scan_job_update_plan(
        action=ScanWorkerAction.CANCEL_JOB,
        job_status=AttachmentScanJobStatus.CANCELLED.value,
        attachment_safety_status=AttachmentSafetyStatus.SCAN_PENDING.value,
    )
    assert_scan_job_update_allowed(_job("queued"), cancel_q)
    assert_scan_job_update_allowed(_job("reserved"), cancel_q)

    with pytest.raises(ScanJobPersistenceError, match="Terminal"):
        assert_scan_job_update_allowed(_job("completed"), passed)
    with pytest.raises(ScanJobPersistenceError, match="Terminal"):
        assert_scan_job_update_allowed(_job("failed"), errored)
    with pytest.raises(ScanJobPersistenceError, match="Terminal"):
        assert_scan_job_update_allowed(_job("cancelled"), cancel_q)

    with pytest.raises(ScanJobPersistenceError, match="Disallowed"):
        assert_scan_job_update_allowed(_job("queued"), passed)
    with pytest.raises(ScanJobPersistenceError, match="Disallowed"):
        assert_scan_job_update_allowed(_job("queued"), errored)

    bad_passed = build_persistable_scan_job_update_plan(
        action=ScanWorkerAction.RESERVE_JOB,
        job_status=AttachmentScanJobStatus.RESERVED.value,
        attachment_safety_status=AttachmentSafetyStatus.SCAN_PASSED.value,
    )
    with pytest.raises(ScanJobPersistenceError, match="scan_passed"):
        assert_scan_job_update_allowed(_job("queued"), bad_passed)

    bad_failed = build_persistable_scan_job_update_plan(
        action=ScanWorkerAction.RESERVE_JOB,
        job_status=AttachmentScanJobStatus.RESERVED.value,
        attachment_safety_status=AttachmentSafetyStatus.SCAN_FAILED.value,
    )
    with pytest.raises(ScanJobPersistenceError, match="scan_failed"):
        assert_scan_job_update_allowed(_job("queued"), bad_failed)

    bad_error = build_persistable_scan_job_update_plan(
        action=ScanWorkerAction.COMPLETE_PASSED,
        job_status=AttachmentScanJobStatus.COMPLETED.value,
        attachment_safety_status=AttachmentSafetyStatus.SCAN_ERROR.value,
    )
    with pytest.raises(ScanJobPersistenceError, match="scan_error"):
        assert_scan_job_update_allowed(_job("reserved"), bad_error)

    quarantined = build_persistable_scan_job_update_plan(
        action=ScanWorkerAction.COMPLETE_FAILED,
        job_status=AttachmentScanJobStatus.COMPLETED.value,
        attachment_safety_status=AttachmentSafetyStatus.QUARANTINED.value,
    )
    with pytest.raises(ScanJobPersistenceError, match="quarantined"):
        assert_scan_job_update_allowed(_job("reserved"), quarantined)


def test_noop_and_disabled_adapter_plans_are_not_persistable() -> None:
    noop_plan = build_scan_job_update_from_result(
        NoopUnavailableScannerAdapter().scan_attachment()
    )
    assert noop_plan.apply_to_database is False
    assert plan_is_persistable(noop_plan) is False
    with pytest.raises(ScanJobPersistenceError, match="not persistable"):
        assert_scan_job_update_allowed(_job("queued"), noop_plan)

    disabled_plan = build_scan_job_update_from_result(
        DisabledLocalProcessScannerAdapter().scan_attachment()
    )
    assert disabled_plan.apply_to_database is False
    assert plan_is_persistable(disabled_plan) is False


def test_normalize_redacts_paths_and_unknown_codes() -> None:
    plan = build_persistable_scan_job_update_plan(
        action=ScanWorkerAction.MARK_ERROR,
        job_status=AttachmentScanJobStatus.FAILED.value,
        attachment_safety_status=AttachmentSafetyStatus.SCAN_ERROR.value,
        safe_error_code="totally_unknown",
        safe_error_message="failed at /tmp/secret.bin local-evidence://x/y",
    )
    assert plan.safe_error_code == "scanner_output_unavailable"
    assert "tmp" not in (plan.safe_error_message or "").lower()
    assert "local-evidence" not in (plan.safe_error_message or "").lower()
    long = "y" * 400
    long_plan = normalize_scan_job_update_plan(
        build_persistable_scan_job_update_plan(
            action=ScanWorkerAction.MARK_ERROR,
            job_status=AttachmentScanJobStatus.FAILED.value,
            attachment_safety_status=AttachmentSafetyStatus.SCAN_ERROR.value,
            safe_error_code="scanner_error",
            safe_error_message=long,
        )
    )
    assert len(long_plan.safe_error_message or "") <= 240


def test_persistence_module_has_no_subprocess_scanner_ocr_llm_raw_fields() -> None:
    source = PERSIST.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
    for mod in imports:
        assert "subprocess" not in mod
        assert "clamav" not in mod
        assert "virustotal" not in mod
        assert "openai" not in mod
        assert "pytesseract" not in mod
    lower = source.lower()
    for forbidden in (
        "import subprocess",
        "raw_output",
        "scanner_stdout",
        "scanner_stderr",
        "clamav",
        "virustotal",
        "app.tools.llm",
        "app.core.config",
        "os.environ",
        "getenv",
    ):
        assert forbidden not in lower, forbidden
    summary = persistence_guard_summary()
    assert summary["mutates_evidence_record"] is False
    assert summary["runs_scanner"] is False
    assert summary["is_verification"] is False


def test_no_scan_routes_ui_or_f0012() -> None:
    paths = set(app.openapi().get("paths", {}))
    for path in paths:
        if path.startswith("/api/v1/evidence"):
            assert "/scan" not in path.lower(), path
            assert "/share" not in path.lower()
            assert "/public" not in path.lower()
        assert not path.startswith("/api/v1/verification")
    for page in FRONTEND_PAGES:
        text = page.read_text(encoding="utf-8").lower()
        for needle in (
            "scan now",
            "rescan",
            "mark safe",
            "mark clean",
            "quarantine",
            "verify file",
        ):
            assert needle not in text, f"{page}: {needle}"
    migrations = (
        REPO_ROOT
        / "backend"
        / "app"
        / "db"
        / "foundation_migrations"
        / "versions"
    )
    assert list(migrations.glob("f0012*")) == []
    assert PERSIST.exists()


@require_disposable_postgres
def test_apply_persistable_plan_updates_only_scan_job() -> None:
    with temporary_database(prefix=F22_PREFIX) as (_name, url):
        prepare_database(url)
        assert foundation_heads() == [F0011]
        user_id = _insert_user(url)

        async def _run() -> None:
            engine = create_async_engine(_async_url(url), pool_pre_ping=True)
            sessions = async_sessionmaker(
                bind=engine, expire_on_commit=False, class_=AsyncSession
            )
            try:
                async with sessions() as db:
                    subject = CareerSubject(owner_user_id=user_id)
                    db.add(subject)
                    await db.commit()
                    await db.refresh(subject)
                    actor = ActorRef(
                        actor_type=ActorType.USER, actor_id=new_entity_id()
                    )
                    evidence = await create_evidence_record(
                        db,
                        owner_user_id=user_id,
                        subject_id=subject.id,
                        title="F22 attached",
                        evidence_kind=EvidenceKind.DOCUMENT,
                        privacy_class=EvidencePrivacyClass.PRIVATE,
                        storage_uri=(
                            f"local-evidence://{user_id}/{uuid.uuid4()}/n.txt"
                        ),
                        content_hash="b" * 64,
                        mime_type="text/plain",
                        size_bytes=4,
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
                        evidence_id=evidence.id,
                        link_role=ClaimEvidenceLinkRole.SUPPORTS,
                        created_by_actor=actor,
                    )
                    review = await create_review_request(
                        db,
                        owner_user_id=user_id,
                        claim_id=claim.id,
                        created_by_actor=actor,
                    )
                    prior_support = claim.support_status
                    prior_verification = claim.verification_status
                    prior_review = review.review_state
                    prior_hash = evidence.content_hash
                    prior_uri = evidence.storage_uri

                    job = await create_attachment_scan_job(
                        db, owner_user_id=user_id, evidence_id=evidence.id
                    )
                    assert job.job_status == "queued"

                    # No-op adapter plan must not write.
                    noop_plan = build_scan_job_update_from_result(
                        NoopUnavailableScannerAdapter().scan_attachment()
                    )
                    with pytest.raises(ScanJobPersistenceError):
                        await apply_scan_job_update_plan(
                            db,
                            job_id=job.id,
                            owner_user_id=user_id,
                            plan=noop_plan,
                        )
                    await db.refresh(job)
                    assert job.job_status == "queued"

                    reserved = await apply_scan_job_update_plan(
                        db,
                        job_id=job.id,
                        owner_user_id=user_id,
                        plan=build_persistable_scan_job_update_plan(
                            action=ScanWorkerAction.RESERVE_JOB,
                            job_status="reserved",
                            attachment_safety_status="scan_pending",
                        ),
                    )
                    assert reserved.job_status == "reserved"
                    assert reserved.attempt_count == 1
                    assert reserved.started_at is not None

                    completed = await apply_scan_job_update_plan(
                        db,
                        job_id=job.id,
                        owner_user_id=user_id,
                        plan=build_persistable_scan_job_update_plan(
                            action=ScanWorkerAction.COMPLETE_PASSED,
                            job_status="completed",
                            attachment_safety_status="scan_passed",
                            engine_name="test-local",
                            engine_version="0",
                        ),
                    )
                    assert completed.job_status == "completed"
                    assert completed.attachment_safety_status == "scan_passed"
                    assert completed.completed_at is not None
                    assert completed.engine_name == "test-local"

                    with pytest.raises(ScanJobPersistenceError, match="Terminal"):
                        await apply_scan_job_update_plan(
                            db,
                            job_id=job.id,
                            owner_user_id=user_id,
                            plan=build_persistable_scan_job_update_plan(
                                action=ScanWorkerAction.RESERVE_JOB,
                                job_status="reserved",
                                attachment_safety_status="scan_pending",
                            ),
                        )

                    await db.refresh(evidence)
                    await db.refresh(claim)
                    await db.refresh(review)
                    assert evidence.content_hash == prior_hash
                    assert evidence.storage_uri == prior_uri
                    assert claim.support_status == prior_support
                    assert claim.verification_status == prior_verification
                    assert review.review_state == prior_review

                    # Cancel path on a fresh job (separate evidence/hash).
                    evidence2 = await create_evidence_record(
                        db,
                        owner_user_id=user_id,
                        subject_id=subject.id,
                        title="F22 attached 2",
                        evidence_kind=EvidenceKind.DOCUMENT,
                        privacy_class=EvidencePrivacyClass.PRIVATE,
                        storage_uri=(
                            f"local-evidence://{user_id}/{uuid.uuid4()}/m.txt"
                        ),
                        content_hash="c" * 64,
                        mime_type="text/plain",
                        size_bytes=2,
                        created_by_actor=actor,
                    )
                    job2 = await create_attachment_scan_job(
                        db,
                        owner_user_id=user_id,
                        evidence_id=evidence2.id,
                    )
                    cancelled = await apply_scan_job_update_plan(
                        db,
                        job_id=job2.id,
                        owner_user_id=user_id,
                        plan=build_persistable_scan_job_update_plan(
                            action=ScanWorkerAction.CANCEL_JOB,
                            job_status="cancelled",
                            attachment_safety_status="scan_pending",
                        ),
                    )
                    assert cancelled.job_status == "cancelled"
                    assert cancelled.cancelled_at is not None
            finally:
                await engine.dispose()

        asyncio.run(_run())
