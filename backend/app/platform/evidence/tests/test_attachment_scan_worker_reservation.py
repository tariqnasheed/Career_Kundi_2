"""Scanner worker reservation guard tests (0053-F27)."""

from __future__ import annotations

import ast
import asyncio
import uuid
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

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
from app.platform.evidence.attachment_safety import AttachmentSafetyStatus
from app.platform.evidence.attachment_scan_queue import (
    AttachmentScanJobStatus,
    create_attachment_scan_job,
)
from app.platform.evidence.attachment_scan_worker_reservation import (
    SCAN_WORKER_RESERVATION_EXECUTES_SCANNER,
    SCAN_WORKER_RESERVATION_EXPOSES_ROUTE,
    SCAN_WORKER_RESERVATION_GUARD_ENABLED,
    SCAN_WORKER_RESERVATION_MUTATES_ONLY_SCAN_JOB,
    SCAN_WORKER_RESERVATION_READS_FILES,
    SCAN_WORKER_RESERVATION_REGISTERS_WORKER,
    ScanWorkerReservationDecision,
    ScanWorkerReservationError,
    assert_scan_worker_reservation_allowed,
    reservation_guard_summary,
    reserve_attachment_scan_job_for_worker,
)
from app.platform.evidence.service import create_evidence_record, link_evidence_to_claim
from app.platform.identity.refs import ActorRef, ActorType
from app.platform.kernel import new_entity_id
from app.platform.verification.service import create_review_request

REPO_ROOT = Path(__file__).resolve().parents[5]
RESERVE_MODULE = (
    REPO_ROOT
    / "backend"
    / "app"
    / "platform"
    / "evidence"
    / "attachment_scan_worker_reservation.py"
)
DRY_RUN_MODULE = (
    REPO_ROOT
    / "backend"
    / "app"
    / "platform"
    / "evidence"
    / "attachment_scan_worker_dry_run.py"
)
EVIDENCE_PKG = REPO_ROOT / "backend" / "app" / "platform" / "evidence"
MAIN_PY = REPO_ROOT / "backend" / "app" / "main.py"
ROUTES = REPO_ROOT / "backend" / "app" / "api" / "routes"
MIGRATIONS = (
    REPO_ROOT / "backend" / "app" / "db" / "foundation_migrations" / "versions"
)
DEP_FILES = [
    REPO_ROOT / "backend" / "requirements.txt",
    REPO_ROOT / "backend" / "pyproject.toml",
    REPO_ROOT / "requirements.txt",
    REPO_ROOT / "pyproject.toml",
]
FRONTEND_PAGES = [
    REPO_ROOT / "frontend" / "src" / "pages" / "EvidenceLibraryPage.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "passport"
    / "PassportEvidencePanel.tsx",
]
# Reuse approved disposable prefix (do not invent new prefixes).
F27_PREFIX = "ck_f2svc_"
F0011 = "f0011_attachment_scan_queue"


def _async_url(sync_url: str) -> str:
    return sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)


def _insert_user(sync_url: str, *, email_prefix: str = "f27") -> uuid.UUID:
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
                    full_name="F27 User",
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


def test_reservation_flags() -> None:
    assert SCAN_WORKER_RESERVATION_GUARD_ENABLED is True
    assert SCAN_WORKER_RESERVATION_EXECUTES_SCANNER is False
    assert SCAN_WORKER_RESERVATION_READS_FILES is False
    assert SCAN_WORKER_RESERVATION_REGISTERS_WORKER is False
    assert SCAN_WORKER_RESERVATION_EXPOSES_ROUTE is False
    assert SCAN_WORKER_RESERVATION_MUTATES_ONLY_SCAN_JOB is True
    summary = reservation_guard_summary()
    assert summary["allowed_transition"] == "queued->reserved"
    assert summary["allowed_row"] == "AttachmentScanJob"
    assert summary["calls_apply_scan_job_update_plan"] is False
    assert summary["calls_scanner_adapter"] is False
    assert summary["emits_audit"] is False
    assert summary["is_scanning"] is False
    assert summary["is_verification"] is False


def test_assert_allows_queued_hash_match() -> None:
    job = SimpleNamespace(
        job_status="queued",
        content_hash_snapshot="a" * 64,
    )
    assert_scan_worker_reservation_allowed(
        job, expected_content_hash_snapshot="a" * 64
    )


def test_assert_rejects_not_queued_and_hash_mismatch() -> None:
    job = SimpleNamespace(
        job_status="reserved",
        content_hash_snapshot="a" * 64,
    )
    with pytest.raises(ScanWorkerReservationError) as exc:
        assert_scan_worker_reservation_allowed(
            job, expected_content_hash_snapshot="a" * 64
        )
    assert exc.value.decision is ScanWorkerReservationDecision.NOT_QUEUED

    job2 = SimpleNamespace(
        job_status="queued",
        content_hash_snapshot="a" * 64,
    )
    with pytest.raises(ScanWorkerReservationError) as exc2:
        assert_scan_worker_reservation_allowed(
            job2, expected_content_hash_snapshot="b" * 64
        )
    assert exc2.value.decision is ScanWorkerReservationDecision.HASH_MISMATCH


def test_module_has_no_forbidden_imports_or_calls() -> None:
    source = RESERVE_MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
            imports.add(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
                imports.add(alias.name)
    for forbidden in (
        "subprocess",
        "pathlib",
        "shutil",
        "os",
        "httpx",
        "requests",
        "aiohttp",
        "celery",
        "apscheduler",
        "fastapi",
        "clamav",
        "virustotal",
        "pytesseract",
        "pdfminer",
        "openai",
        "anthropic",
        "groq",
        "together",
        "app.tools.llm",
        "app.platform.evidence.attachment_scan_result_persistence",
        "app.platform.evidence.attachment_scanner_adapter",
        "app.platform.evidence.attachment_local_scanner_adapter",
        "app.platform.evidence.attachment_quarantine_audit",
        "app.platform.evidence.attachment_quarantine_storage",
        "app.platform.evidence.storage",
    ):
        assert forbidden not in imports, forbidden
    for needle in (
        "import subprocess",
        "apply_scan_job_update_plan(",
        "from app.platform.evidence.attachment_scan_result_persistence",
        "get_scanner_adapter(",
        "NoopUnavailableScannerAdapter",
        "DisabledLocalProcessScannerAdapter",
        "emit_quarantine",
        "record_quarantine",
        "open(",
        "Path(",
        "read_bytes",
        "BackgroundTasks",
        "asyncio.create_task",
            "while True",
        ):
        assert needle not in source, needle
    # Class names must not appear as imports/usages (docstring-safe wording only).
    tree_src = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree_src):
        if isinstance(node, ast.Name):
            names.add(node.id)
        if isinstance(node, ast.Attribute):
            names.add(node.attr)
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.name)
    for forbidden_name in ("EvidenceRecord", "ClaimRecord", "ReviewRequest"):
        assert forbidden_name not in names, forbidden_name


def test_no_worker_loop_or_startup_registration() -> None:
    main_src = MAIN_PY.read_text(encoding="utf-8")
    for needle in (
        "attachment_scan_worker_reservation",
        "reserve_attachment_scan_job_for_worker",
        "attachment_scan_worker_dry_run",
        "register_scan_worker",
        "start_scan_worker",
    ):
        assert needle not in main_src, needle
    source = RESERVE_MODULE.read_text(encoding="utf-8")
    assert "while True" not in source
    assert "def run_worker" not in source
    assert "def start_worker" not in source
    dry_summary_src = DRY_RUN_MODULE.read_text(encoding="utf-8")
    assert "reservation_guard_exists" in dry_summary_src
    assert "calls_reserve_attachment_scan_job_for_worker" in dry_summary_src


def test_no_worker_admin_scan_quarantine_audit_routes() -> None:
    paths = set(app.openapi().get("paths", {}))
    for path in paths:
        lower = path.lower()
        if path.startswith("/api/v1/evidence"):
            for needle in (
                "/scan",
                "/quarantine",
                "/audit",
                "/admin",
                "/worker",
                "/rescan",
                "/reserve",
            ):
                assert needle not in lower, path
        assert not path.startswith("/api/v1/verification")
        assert not path.startswith("/api/v1/admin")
        assert "/worker" not in lower
    assert not (ROUTES / "scan_worker.py").exists()
    assert not (ROUTES / "admin_scan.py").exists()
    assert not (ROUTES / "audit.py").exists()
    assert not (ROUTES / "quarantine.py").exists()


def test_no_frontend_worker_admin_scan_ui() -> None:
    for page in FRONTEND_PAGES:
        text = page.read_text(encoding="utf-8").lower()
        for needle in (
            "scan now",
            "rescan",
            "mark safe",
            "mark clean",
            "quarantine",
            "audit log",
            "admin panel",
            "run worker",
            "start worker",
            "reserve scan",
            "verify file",
        ):
            assert needle not in text, f"{page}: {needle}"


def test_no_db_migration_or_scanner_dependency() -> None:
    for name in ("f0012", "f0013", "f0014"):
        assert list(MIGRATIONS.glob(f"{name}*")) == []
    assert list(MIGRATIONS.glob("f0011*")) == [
        MIGRATIONS / "f0011_attachment_scan_queue.py"
    ]
    dep_text = ""
    for path in DEP_FILES:
        if path.exists():
            dep_text += "\n" + path.read_text(encoding="utf-8").lower()
    assert dep_text, "expected dependency manifest"
    for needle in ("clamav", "virustotal", "pytesseract", "pdfminer", "openai"):
        assert needle not in dep_text, needle


@require_disposable_postgres
def test_reserve_queued_owned_job_and_boundaries() -> None:
    with temporary_database(prefix=F27_PREFIX) as (_name, url):
        prepare_database(url)
        assert foundation_heads() == [F0011]
        user_id = _insert_user(url)
        other_id = _insert_user(url, email_prefix="f27other")

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
                    content_hash = "d" * 64
                    evidence = await create_evidence_record(
                        db,
                        owner_user_id=user_id,
                        subject_id=subject.id,
                        title="F27 attached",
                        evidence_kind=EvidenceKind.DOCUMENT,
                        privacy_class=EvidencePrivacyClass.PRIVATE,
                        storage_uri=(
                            f"local-evidence://{user_id}/{uuid.uuid4()}/n.txt"
                        ),
                        content_hash=content_hash,
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
                    prior_safety = AttachmentSafetyStatus.SCAN_PENDING.value

                    job = await create_attachment_scan_job(
                        db, owner_user_id=user_id, evidence_id=evidence.id
                    )
                    assert job.job_status == AttachmentScanJobStatus.QUEUED.value
                    assert job.attempt_count == 0
                    assert job.started_at is None
                    assert job.completed_at is None
                    assert job.engine_name is None
                    assert job.safe_error_code is None

                    # Hash mismatch rejects.
                    mismatch = await reserve_attachment_scan_job_for_worker(
                        db,
                        job_id=job.id,
                        owner_user_id=user_id,
                        expected_content_hash_snapshot="e" * 64,
                    )
                    assert mismatch.reserved is False
                    assert (
                        mismatch.decision
                        is ScanWorkerReservationDecision.HASH_MISMATCH
                    )
                    await db.refresh(job)
                    assert job.job_status == "queued"
                    assert job.attempt_count == 0

                    # Other owner cannot reserve (safe not-found).
                    other = await reserve_attachment_scan_job_for_worker(
                        db,
                        job_id=job.id,
                        owner_user_id=other_id,
                        expected_content_hash_snapshot=content_hash,
                    )
                    assert other.reserved is False
                    assert other.decision is ScanWorkerReservationDecision.NOT_FOUND

                    # Missing job.
                    missing = await reserve_attachment_scan_job_for_worker(
                        db,
                        job_id=uuid.uuid4(),
                        owner_user_id=user_id,
                        expected_content_hash_snapshot=content_hash,
                    )
                    assert missing.reserved is False
                    assert missing.decision is ScanWorkerReservationDecision.NOT_FOUND

                    # No persistence / adapter / audit / storage calls during reserve.
                    with (
                        patch(
                            "app.platform.evidence.attachment_scan_result_persistence"
                            ".apply_scan_job_update_plan",
                            new_callable=AsyncMock,
                        ) as mock_persist,
                        patch(
                            "app.platform.evidence.attachment_scanner_adapter"
                            ".get_configured_attachment_scanner_adapter",
                            new_callable=MagicMock,
                        ) as mock_adapter,
                        patch(
                            "app.platform.evidence.attachment_quarantine_audit"
                            ".build_quarantine_audit_event",
                            new_callable=MagicMock,
                        ) as mock_audit,
                        patch(
                            "app.platform.evidence.storage.open_evidence_file",
                            new_callable=MagicMock,
                        ) as mock_storage,
                    ):
                        result = await reserve_attachment_scan_job_for_worker(
                            db,
                            job_id=job.id,
                            owner_user_id=user_id,
                            expected_content_hash_snapshot=content_hash,
                        )
                        mock_persist.assert_not_called()
                        mock_adapter.assert_not_called()
                        mock_audit.assert_not_called()
                        mock_storage.assert_not_called()

                    assert result.reserved is True
                    assert result.decision is ScanWorkerReservationDecision.RESERVED
                    assert result.previous_status == "queued"
                    assert result.new_status == "reserved"
                    assert result.attempt_count == 1

                    await db.refresh(job)
                    assert job.job_status == AttachmentScanJobStatus.RESERVED.value
                    assert job.attempt_count == 1
                    assert job.started_at is not None
                    assert job.completed_at is None
                    assert job.cancelled_at is None
                    assert job.attachment_safety_status == prior_safety
                    assert job.engine_name is None
                    assert job.engine_version is None
                    assert job.safe_error_code is None
                    assert job.safe_error_message is None

                    # Already reserved cannot reserve again.
                    again = await reserve_attachment_scan_job_for_worker(
                        db,
                        job_id=job.id,
                        owner_user_id=user_id,
                        expected_content_hash_snapshot=content_hash,
                    )
                    assert again.reserved is False
                    assert again.decision is ScanWorkerReservationDecision.NOT_QUEUED
                    await db.refresh(job)
                    assert job.attempt_count == 1

                    await db.refresh(evidence)
                    await db.refresh(claim)
                    await db.refresh(review)
                    assert evidence.content_hash == prior_hash
                    assert evidence.storage_uri == prior_uri
                    assert claim.support_status == prior_support
                    assert claim.verification_status == prior_verification
                    assert review.review_state == prior_review

                    # Terminal statuses cannot be reserved.
                    for terminal, field in (
                        ("completed", "completed_at"),
                        ("failed", "completed_at"),
                        ("cancelled", "cancelled_at"),
                    ):
                        ev = await create_evidence_record(
                            db,
                            owner_user_id=user_id,
                            subject_id=subject.id,
                            title=f"F27 {terminal}",
                            evidence_kind=EvidenceKind.DOCUMENT,
                            privacy_class=EvidencePrivacyClass.PRIVATE,
                            storage_uri=(
                                f"local-evidence://{user_id}/{uuid.uuid4()}/t.txt"
                            ),
                            content_hash=uuid.uuid4().hex + uuid.uuid4().hex[:32],
                            mime_type="text/plain",
                            size_bytes=2,
                            created_by_actor=actor,
                        )
                        tjob = await create_attachment_scan_job(
                            db,
                            owner_user_id=user_id,
                            evidence_id=ev.id,
                        )
                        tjob.job_status = terminal
                        setattr(
                            tjob,
                            field,
                            datetime.now(timezone.utc),
                        )
                        await db.commit()
                        await db.refresh(tjob)
                        denied = await reserve_attachment_scan_job_for_worker(
                            db,
                            job_id=tjob.id,
                            owner_user_id=user_id,
                            expected_content_hash_snapshot=tjob.content_hash_snapshot,
                        )
                        assert denied.reserved is False
                        assert (
                            denied.decision
                            is ScanWorkerReservationDecision.NOT_QUEUED
                        )
                        await db.refresh(tjob)
                        assert tjob.job_status == terminal
                        assert tjob.attempt_count == 0
            finally:
                await engine.dispose()

        asyncio.run(_run())
