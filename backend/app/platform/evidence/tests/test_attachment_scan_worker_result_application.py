"""Scanner worker result application guard tests (0053-F29)."""

from __future__ import annotations

import ast
import asyncio
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.db.migration_runner import foundation_heads, prepare_database
from app.db.models.attachment_scan import AttachmentScanJob
from app.db.models.career_subject import CareerSubject
from app.db.models.evidence import EvidenceRecord
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
    cancel_attachment_scan_job,
    create_attachment_scan_job,
)
from app.platform.evidence.attachment_scan_result_persistence import (
    apply_scan_job_update_plan,
    build_persistable_scan_job_update_plan,
)
from app.platform.evidence.attachment_scan_worker import ScanWorkerAction
from app.platform.evidence.attachment_scan_worker_dry_run import (
    SCAN_WORKER_DB_MUTATION_ENABLED,
    SCAN_WORKER_DRY_RUN_ENABLED,
    SCAN_WORKER_ENABLED,
    current_scan_worker_dry_run_plan,
)
from app.platform.evidence.attachment_scan_worker_reservation import (
    ScanWorkerReservationDecision,
    reserve_attachment_scan_job_for_worker,
)
from app.platform.evidence.attachment_scan_worker_result_application import (
    SCAN_WORKER_RESULT_APPLICATION_EXECUTES_SCANNER,
    SCAN_WORKER_RESULT_APPLICATION_EXPOSES_ROUTE,
    SCAN_WORKER_RESULT_APPLICATION_GUARD_ENABLED,
    SCAN_WORKER_RESULT_APPLICATION_LOCK_ORDER,
    SCAN_WORKER_RESULT_APPLICATION_MUTATES_ONLY_SCAN_JOB,
    SCAN_WORKER_RESULT_APPLICATION_READS_FILES,
    SCAN_WORKER_RESULT_APPLICATION_REGISTERS_WORKER,
    ScanWorkerResultApplicationDecision,
    apply_attachment_scan_worker_result,
    assert_f29_result_plan_allowed,
    result_application_guard_summary,
)
from app.platform.evidence.service import create_evidence_record, link_evidence_to_claim
from app.platform.identity.refs import ActorRef, ActorType
from app.platform.kernel import new_entity_id
from app.platform.verification.service import create_review_request

REPO_ROOT = Path(__file__).resolve().parents[5]
APPLY_MODULE = (
    REPO_ROOT
    / "backend"
    / "app"
    / "platform"
    / "evidence"
    / "attachment_scan_worker_result_application.py"
)
PERSIST_MODULE = (
    REPO_ROOT
    / "backend"
    / "app"
    / "platform"
    / "evidence"
    / "attachment_scan_result_persistence.py"
)
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
F29_PREFIX = "ck_f2svc_"
F0011 = "f0011_attachment_scan_queue"


def _async_url(sync_url: str) -> str:
    return sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)


def _insert_user(sync_url: str, *, email_prefix: str = "f29") -> uuid.UUID:
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
                    full_name="F29 User",
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


def _passed_plan(**kwargs):
    return build_persistable_scan_job_update_plan(
        action=ScanWorkerAction.COMPLETE_PASSED,
        job_status=AttachmentScanJobStatus.COMPLETED.value,
        attachment_safety_status=AttachmentSafetyStatus.SCAN_PASSED.value,
        engine_name=kwargs.pop("engine_name", "test-engine"),
        engine_version=kwargs.pop("engine_version", "1"),
        **kwargs,
    )


def _failed_plan(**kwargs):
    return build_persistable_scan_job_update_plan(
        action=ScanWorkerAction.COMPLETE_FAILED,
        job_status=AttachmentScanJobStatus.COMPLETED.value,
        attachment_safety_status=AttachmentSafetyStatus.SCAN_FAILED.value,
        safe_error_code=kwargs.pop("safe_error_code", "scanner_error"),
        safe_error_message=kwargs.pop(
            "safe_error_message", "concerning attachment result"
        ),
        engine_name=kwargs.pop("engine_name", "test-engine"),
        engine_version=kwargs.pop("engine_version", "1"),
        **kwargs,
    )


def _error_plan(**kwargs):
    return build_persistable_scan_job_update_plan(
        action=ScanWorkerAction.MARK_ERROR,
        job_status=AttachmentScanJobStatus.FAILED.value,
        attachment_safety_status=AttachmentSafetyStatus.SCAN_ERROR.value,
        safe_error_code=kwargs.pop("safe_error_code", "scanner_timeout"),
        safe_error_message=kwargs.pop("safe_error_message", "timed out"),
        engine_name=kwargs.pop("engine_name", "test-engine"),
        engine_version=kwargs.pop("engine_version", "1"),
        **kwargs,
    )


def _quarantine_plan(**kwargs):
    return build_persistable_scan_job_update_plan(
        action=ScanWorkerAction.QUARANTINE_REQUIRED,
        job_status=AttachmentScanJobStatus.COMPLETED.value,
        attachment_safety_status=AttachmentSafetyStatus.SCAN_FAILED.value,
        safe_error_code=kwargs.pop("safe_error_code", "malicious"),
        safe_error_message=kwargs.pop(
            "safe_error_message", "Scanner reported a concerning attachment result."
        ),
        quarantine_required=True,
        engine_name=kwargs.pop("engine_name", "test-engine"),
        engine_version=kwargs.pop("engine_version", "1"),
        **kwargs,
    )


def test_result_application_flags() -> None:
    assert SCAN_WORKER_RESULT_APPLICATION_GUARD_ENABLED is True
    assert SCAN_WORKER_RESULT_APPLICATION_EXECUTES_SCANNER is False
    assert SCAN_WORKER_RESULT_APPLICATION_READS_FILES is False
    assert SCAN_WORKER_RESULT_APPLICATION_REGISTERS_WORKER is False
    assert SCAN_WORKER_RESULT_APPLICATION_EXPOSES_ROUTE is False
    assert SCAN_WORKER_RESULT_APPLICATION_MUTATES_ONLY_SCAN_JOB is True
    assert (
        SCAN_WORKER_RESULT_APPLICATION_LOCK_ORDER
        == "attachment_scan_job_then_evidence_record"
    )
    summary = result_application_guard_summary()
    assert summary["allowed_row"] == "AttachmentScanJob"
    assert summary["calls_public_apply_scan_job_update_plan"] is False
    assert summary["calls_scanner_adapter"] is False
    assert summary["emits_audit"] is False
    assert summary["mutates_evidence_record"] is False
    assert summary["is_scanning"] is False
    assert summary["is_verification"] is False
    assert summary["idempotency_projection"] == [
        "job_status",
        "attachment_safety_status",
        "engine_name",
        "engine_version",
        "safe_error_code",
        "safe_error_message",
    ]


def test_assert_f29_rejects_cancel_reserve_noop() -> None:
    assert_f29_result_plan_allowed(_passed_plan())
    assert_f29_result_plan_allowed(_failed_plan())
    assert_f29_result_plan_allowed(_error_plan())
    assert_f29_result_plan_allowed(_quarantine_plan())

    cancel = build_persistable_scan_job_update_plan(
        action=ScanWorkerAction.CANCEL_JOB,
        job_status=AttachmentScanJobStatus.CANCELLED.value,
        attachment_safety_status=AttachmentSafetyStatus.SCAN_PENDING.value,
    )
    with pytest.raises(Exception) as exc:
        assert_f29_result_plan_allowed(cancel)
    assert exc.value.decision is ScanWorkerResultApplicationDecision.ACTION_NOT_ALLOWED

    reserve = build_persistable_scan_job_update_plan(
        action=ScanWorkerAction.RESERVE_JOB,
        job_status=AttachmentScanJobStatus.RESERVED.value,
        attachment_safety_status=AttachmentSafetyStatus.SCAN_PENDING.value,
    )
    with pytest.raises(Exception) as exc2:
        assert_f29_result_plan_allowed(reserve)
    assert (
        exc2.value.decision is ScanWorkerResultApplicationDecision.ACTION_NOT_ALLOWED
    )

    from dataclasses import replace

    noop = replace(_passed_plan(), action=ScanWorkerAction.NO_OP, apply_to_database=False)
    with pytest.raises(Exception) as exc3:
        assert_f29_result_plan_allowed(noop)
    assert (
        exc3.value.decision
        is ScanWorkerResultApplicationDecision.PLAN_NOT_PERSISTABLE
    )


def test_module_has_no_forbidden_imports_or_calls() -> None:
    source = APPLY_MODULE.read_text(encoding="utf-8")
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
    # Must use FOR UPDATE lock helpers and shared F22 mutate helper.
    assert "with_for_update" in source
    assert "apply_normalized_scan_job_update_to_loaded_job" in source
    assert "normalize_scan_job_update_plan" in source
    assert "assert_scan_job_update_allowed" in source
    # Must not call public unlocked F22 apply as outer txn.
    assert "calls_public_apply_scan_job_update_plan" in source
    persist_src = PERSIST_MODULE.read_text(encoding="utf-8")
    assert "def apply_normalized_scan_job_update_to_loaded_job" in persist_src


def test_no_worker_loop_or_startup_registration() -> None:
    main_src = MAIN_PY.read_text(encoding="utf-8")
    for needle in (
        "attachment_scan_worker_result_application",
        "apply_attachment_scan_worker_result",
        "attachment_scan_worker_dry_run",
        "register_scan_worker",
        "start_scan_worker",
    ):
        assert needle not in main_src, needle
    source = APPLY_MODULE.read_text(encoding="utf-8")
    assert "while True" not in source
    assert "def run_worker" not in source
    assert "def start_worker" not in source


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
                "/apply-result",
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
            "apply scan result",
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


def test_f26_dry_run_remains_disabled() -> None:
    assert SCAN_WORKER_ENABLED is False
    assert SCAN_WORKER_DRY_RUN_ENABLED is False
    assert SCAN_WORKER_DB_MUTATION_ENABLED is False
    plan = current_scan_worker_dry_run_plan()
    assert plan.runner_enabled is False
    assert plan.db_mutation_enabled is False
    dry_src = DRY_RUN_MODULE.read_text(encoding="utf-8")
    assert "apply_attachment_scan_worker_result" not in dry_src


@require_disposable_postgres
def test_apply_owner_guards_transitions_idempotency_and_boundaries() -> None:
    with temporary_database(prefix=F29_PREFIX) as (_name, url):
        prepare_database(url)
        assert foundation_heads() == [F0011]
        user_id = _insert_user(url)
        other_id = _insert_user(url, email_prefix="f29other")

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
                    subject_id = subject.id
                    actor = ActorRef(
                        actor_type=ActorType.USER, actor_id=new_entity_id()
                    )
                    content_hash = "a" * 64
                    evidence = await create_evidence_record(
                        db,
                        owner_user_id=user_id,
                        subject_id=subject_id,
                        title="F29 attached",
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
                        subject_id=subject_id,
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
                    evidence_id = evidence.id
                    prior_hash = evidence.content_hash
                    prior_uri = evidence.storage_uri
                    prior_mime = evidence.mime_type
                    prior_size = evidence.size_bytes
                    prior_title = evidence.title

                    job = await create_attachment_scan_job(
                        db, owner_user_id=user_id, evidence_id=evidence_id
                    )
                    job_id = job.id
                    # Queued source rejected.
                    queued_reject = await apply_attachment_scan_worker_result(
                        db,
                        owner_user_id=user_id,
                        scan_job_id=job_id,
                        expected_content_hash_snapshot=content_hash,
                        plan=_passed_plan(),
                    )
                    assert queued_reject.applied is False
                    assert (
                        queued_reject.decision
                        is ScanWorkerResultApplicationDecision.NOT_RESERVED
                    )
                    await db.refresh(job)
                    assert job.job_status == "queued"

                    reserved = await reserve_attachment_scan_job_for_worker(
                        db,
                        job_id=job_id,
                        owner_user_id=user_id,
                        expected_content_hash_snapshot=content_hash,
                    )
                    assert reserved.decision is ScanWorkerReservationDecision.RESERVED
                    await db.refresh(job)
                    started_at = job.started_at
                    attempt_before = job.attempt_count
                    assert started_at is not None
                    assert attempt_before == 1

                    # Other owner → safe not-found.
                    other = await apply_attachment_scan_worker_result(
                        db,
                        owner_user_id=other_id,
                        scan_job_id=job_id,
                        expected_content_hash_snapshot=content_hash,
                        plan=_passed_plan(),
                    )
                    assert other.applied is False
                    assert (
                        other.decision
                        is ScanWorkerResultApplicationDecision.NOT_FOUND
                    )
                    await db.refresh(job)
                    assert job.job_status == "reserved"

                    # Missing scan job.
                    missing = await apply_attachment_scan_worker_result(
                        db,
                        owner_user_id=user_id,
                        scan_job_id=uuid.uuid4(),
                        expected_content_hash_snapshot=content_hash,
                        plan=_passed_plan(),
                    )
                    assert missing.decision is (
                        ScanWorkerResultApplicationDecision.NOT_FOUND
                    )

                    # Expected hash mismatch.
                    bad_expected = await apply_attachment_scan_worker_result(
                        db,
                        owner_user_id=user_id,
                        scan_job_id=job_id,
                        expected_content_hash_snapshot="b" * 64,
                        plan=_passed_plan(),
                    )
                    assert (
                        bad_expected.decision
                        is ScanWorkerResultApplicationDecision.HASH_MISMATCH
                    )
                    await db.refresh(job)
                    assert job.job_status == "reserved"

                    # Live evidence hash drift.
                    evidence.content_hash = "c" * 64
                    await db.commit()
                    await db.refresh(evidence)
                    await db.refresh(job)
                    drift = await apply_attachment_scan_worker_result(
                        db,
                        owner_user_id=user_id,
                        scan_job_id=job_id,
                        expected_content_hash_snapshot=content_hash,
                        plan=_passed_plan(),
                    )
                    assert (
                        drift.decision
                        is ScanWorkerResultApplicationDecision.HASH_MISMATCH
                    )
                    await db.refresh(evidence)
                    evidence.content_hash = content_hash
                    await db.commit()
                    await db.refresh(evidence)
                    await db.refresh(job)
                    assert job.job_status == "reserved"

                    # CANCEL_JOB / RESERVE_JOB / NO_OP rejected.
                    cancel = await apply_attachment_scan_worker_result(
                        db,
                        owner_user_id=user_id,
                        scan_job_id=job_id,
                        expected_content_hash_snapshot=content_hash,
                        plan=build_persistable_scan_job_update_plan(
                            action=ScanWorkerAction.CANCEL_JOB,
                            job_status="cancelled",
                            attachment_safety_status="scan_pending",
                        ),
                    )
                    assert (
                        cancel.decision
                        is ScanWorkerResultApplicationDecision.ACTION_NOT_ALLOWED
                    )
                    await db.refresh(job)
                    reserve_plan = await apply_attachment_scan_worker_result(
                        db,
                        owner_user_id=user_id,
                        scan_job_id=job_id,
                        expected_content_hash_snapshot=content_hash,
                        plan=build_persistable_scan_job_update_plan(
                            action=ScanWorkerAction.RESERVE_JOB,
                            job_status="reserved",
                            attachment_safety_status="scan_pending",
                        ),
                    )
                    assert (
                        reserve_plan.decision
                        is ScanWorkerResultApplicationDecision.ACTION_NOT_ALLOWED
                    )
                    await db.refresh(job)
                    from dataclasses import replace

                    noop = await apply_attachment_scan_worker_result(
                        db,
                        owner_user_id=user_id,
                        scan_job_id=job_id,
                        expected_content_hash_snapshot=content_hash,
                        plan=replace(
                            _passed_plan(),
                            action=ScanWorkerAction.NO_OP,
                            apply_to_database=False,
                        ),
                    )
                    assert (
                        noop.decision
                        is ScanWorkerResultApplicationDecision.PLAN_NOT_PERSISTABLE
                    )
                    await db.refresh(job)
                    assert job.job_status == "reserved"

                    # First apply: reserved -> completed / scan_passed.
                    with (
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
                        patch(
                            "app.platform.evidence.attachment_scan_result_persistence"
                            ".apply_scan_job_update_plan",
                            new_callable=AsyncMock,
                        ) as mock_public_apply,
                    ):
                        applied = await apply_attachment_scan_worker_result(
                            db,
                            owner_user_id=user_id,
                            scan_job_id=job_id,
                            expected_content_hash_snapshot=content_hash,
                            plan=_passed_plan(
                                engine_name="f29-engine",
                                engine_version="9",
                            ),
                        )
                        mock_adapter.assert_not_called()
                        mock_audit.assert_not_called()
                        mock_storage.assert_not_called()
                        mock_public_apply.assert_not_called()

                    assert applied.applied is True
                    assert (
                        applied.decision
                        is ScanWorkerResultApplicationDecision.APPLIED
                    )
                    await db.refresh(job)
                    assert job.job_status == "completed"
                    assert job.attachment_safety_status == "scan_passed"
                    assert job.engine_name == "f29-engine"
                    assert job.engine_version == "9"
                    assert job.attempt_count == attempt_before
                    assert job.started_at == started_at
                    assert job.completed_at is not None
                    first_completed_at = job.completed_at
                    first_updated_at = job.updated_at
                    assert job.cancelled_at is None

                    # Exact six-field replay → already_applied; timestamps stable.
                    replay = await apply_attachment_scan_worker_result(
                        db,
                        owner_user_id=user_id,
                        scan_job_id=job_id,
                        expected_content_hash_snapshot=content_hash,
                        plan=_passed_plan(
                            engine_name="f29-engine",
                            engine_version="9",
                        ),
                    )
                    assert replay.applied is False
                    assert (
                        replay.decision
                        is ScanWorkerResultApplicationDecision.ALREADY_APPLIED
                    )
                    await db.refresh(job)
                    assert job.completed_at == first_completed_at
                    assert job.updated_at == first_updated_at
                    assert job.attempt_count == attempt_before
                    assert job.started_at == started_at

                    # None engine values preserve stored (F22 non-overwrite).
                    from dataclasses import replace as dc_replace

                    none_engine_replay = await apply_attachment_scan_worker_result(
                        db,
                        owner_user_id=user_id,
                        scan_job_id=job_id,
                        expected_content_hash_snapshot=content_hash,
                        plan=dc_replace(
                            _passed_plan(),
                            engine_name=None,
                            engine_version=None,
                        ),
                    )
                    assert (
                        none_engine_replay.decision
                        is ScanWorkerResultApplicationDecision.ALREADY_APPLIED
                    )
                    await db.refresh(job)
                    assert job.engine_name == "f29-engine"
                    assert job.engine_version == "9"
                    assert job.updated_at == first_updated_at

                    # Conflicting replay on engine field.
                    conflict_engine = await apply_attachment_scan_worker_result(
                        db,
                        owner_user_id=user_id,
                        scan_job_id=job_id,
                        expected_content_hash_snapshot=content_hash,
                        plan=_passed_plan(
                            engine_name="other-engine",
                            engine_version="9",
                        ),
                    )
                    assert (
                        conflict_engine.decision
                        is ScanWorkerResultApplicationDecision.CONFLICTING_REPLAY
                    )
                    await db.refresh(job)
                    assert job.engine_name == "f29-engine"
                    assert job.updated_at == first_updated_at

                    await db.refresh(evidence)
                    await db.refresh(claim)
                    await db.refresh(review)
                    assert evidence.content_hash == prior_hash
                    assert evidence.storage_uri == prior_uri
                    assert evidence.mime_type == prior_mime
                    assert evidence.size_bytes == prior_size
                    assert evidence.title == prior_title
                    assert claim.support_status == prior_support
                    assert claim.verification_status == prior_verification
                    assert review.review_state == prior_review

                    # --- scan_failed path ---
                    ev2 = await create_evidence_record(
                        db,
                        owner_user_id=user_id,
                        subject_id=subject_id,
                        title="F29 failed",
                        evidence_kind=EvidenceKind.DOCUMENT,
                        privacy_class=EvidencePrivacyClass.PRIVATE,
                        storage_uri=(
                            f"local-evidence://{user_id}/{uuid.uuid4()}/f.txt"
                        ),
                        content_hash="d" * 64,
                        mime_type="text/plain",
                        size_bytes=2,
                        created_by_actor=actor,
                    )
                    job2 = await create_attachment_scan_job(
                        db, owner_user_id=user_id, evidence_id=ev2.id
                    )
                    await reserve_attachment_scan_job_for_worker(
                        db,
                        job_id=job2.id,
                        owner_user_id=user_id,
                        expected_content_hash_snapshot="d" * 64,
                    )
                    failed_apply = await apply_attachment_scan_worker_result(
                        db,
                        owner_user_id=user_id,
                        scan_job_id=job2.id,
                        expected_content_hash_snapshot="d" * 64,
                        plan=_failed_plan(),
                    )
                    assert failed_apply.decision is (
                        ScanWorkerResultApplicationDecision.APPLIED
                    )
                    await db.refresh(job2)
                    assert job2.job_status == "completed"
                    assert job2.attachment_safety_status == "scan_failed"
                    assert job2.attachment_safety_status != "quarantined"

                    # Conflicting replay on safe_error_message.
                    conflict_msg = await apply_attachment_scan_worker_result(
                        db,
                        owner_user_id=user_id,
                        scan_job_id=job2.id,
                        expected_content_hash_snapshot="d" * 64,
                        plan=_failed_plan(
                            safe_error_message="different message entirely"
                        ),
                    )
                    assert conflict_msg.decision is (
                        ScanWorkerResultApplicationDecision.CONFLICTING_REPLAY
                    )

                    # --- MARK_ERROR + F21 normalization / redaction ---
                    ev3 = await create_evidence_record(
                        db,
                        owner_user_id=user_id,
                        subject_id=subject_id,
                        title="F29 error",
                        evidence_kind=EvidenceKind.DOCUMENT,
                        privacy_class=EvidencePrivacyClass.PRIVATE,
                        storage_uri=(
                            f"local-evidence://{user_id}/{uuid.uuid4()}/e.txt"
                        ),
                        content_hash="e" * 64,
                        mime_type="text/plain",
                        size_bytes=2,
                        created_by_actor=actor,
                    )
                    job3 = await create_attachment_scan_job(
                        db, owner_user_id=user_id, evidence_id=ev3.id
                    )
                    await reserve_attachment_scan_job_for_worker(
                        db,
                        job_id=job3.id,
                        owner_user_id=user_id,
                        expected_content_hash_snapshot="e" * 64,
                    )
                    err_apply = await apply_attachment_scan_worker_result(
                        db,
                        owner_user_id=user_id,
                        scan_job_id=job3.id,
                        expected_content_hash_snapshot="e" * 64,
                        plan=_error_plan(
                            safe_error_code="totally_unknown",
                            safe_error_message=(
                                "failed at /tmp/secret.bin local-evidence://x/y"
                            ),
                        ),
                    )
                    assert err_apply.decision is (
                        ScanWorkerResultApplicationDecision.APPLIED
                    )
                    await db.refresh(job3)
                    assert job3.job_status == "failed"
                    assert job3.attachment_safety_status == "scan_error"
                    assert job3.safe_error_code == "scanner_output_unavailable"
                    assert "tmp" not in (job3.safe_error_message or "").lower()
                    assert "local-evidence" not in (
                        job3.safe_error_message or ""
                    ).lower()

                    # --- QUARANTINE_REQUIRED stays scan_failed ---
                    ev4 = await create_evidence_record(
                        db,
                        owner_user_id=user_id,
                        subject_id=subject_id,
                        title="F29 quarantine",
                        evidence_kind=EvidenceKind.DOCUMENT,
                        privacy_class=EvidencePrivacyClass.PRIVATE,
                        storage_uri=(
                            f"local-evidence://{user_id}/{uuid.uuid4()}/q.txt"
                        ),
                        content_hash="f" * 64,
                        mime_type="text/plain",
                        size_bytes=2,
                        created_by_actor=actor,
                    )
                    job4 = await create_attachment_scan_job(
                        db, owner_user_id=user_id, evidence_id=ev4.id
                    )
                    await reserve_attachment_scan_job_for_worker(
                        db,
                        job_id=job4.id,
                        owner_user_id=user_id,
                        expected_content_hash_snapshot="f" * 64,
                    )
                    q_apply = await apply_attachment_scan_worker_result(
                        db,
                        owner_user_id=user_id,
                        scan_job_id=job4.id,
                        expected_content_hash_snapshot="f" * 64,
                        plan=_quarantine_plan(),
                    )
                    assert q_apply.decision is (
                        ScanWorkerResultApplicationDecision.APPLIED
                    )
                    await db.refresh(job4)
                    assert job4.job_status == "completed"
                    assert job4.attachment_safety_status == "scan_failed"
                    assert job4.attachment_safety_status != "quarantined"

                    # Missing owner-scoped EvidenceRecord.
                    ev5 = await create_evidence_record(
                        db,
                        owner_user_id=user_id,
                        subject_id=subject_id,
                        title="F29 missing evidence",
                        evidence_kind=EvidenceKind.DOCUMENT,
                        privacy_class=EvidencePrivacyClass.PRIVATE,
                        storage_uri=(
                            f"local-evidence://{user_id}/{uuid.uuid4()}/m.txt"
                        ),
                        content_hash="1" * 64,
                        mime_type="text/plain",
                        size_bytes=2,
                        created_by_actor=actor,
                    )
                    job5 = await create_attachment_scan_job(
                        db, owner_user_id=user_id, evidence_id=ev5.id
                    )
                    await reserve_attachment_scan_job_for_worker(
                        db,
                        job_id=job5.id,
                        owner_user_id=user_id,
                        expected_content_hash_snapshot="1" * 64,
                    )
                    # Owner-scoped evidence miss after job lock (FK-safe simulation).
                    with patch(
                        "app.platform.evidence.attachment_scan_worker_result_application"
                        "._lock_owner_scoped_evidence",
                        new_callable=AsyncMock,
                        return_value=None,
                    ):
                        missing_ev = await apply_attachment_scan_worker_result(
                            db,
                            owner_user_id=user_id,
                            scan_job_id=job5.id,
                            expected_content_hash_snapshot="1" * 64,
                            plan=_passed_plan(),
                        )
                    assert missing_ev.decision is (
                        ScanWorkerResultApplicationDecision.EVIDENCE_NOT_FOUND
                    )
                    await db.refresh(job5)
                    assert job5.job_status == "reserved"

                    # Evidence belongs to another owner.
                    other_subject = CareerSubject(owner_user_id=other_id)
                    db.add(other_subject)
                    await db.commit()
                    await db.refresh(other_subject)
                    other_ev = await create_evidence_record(
                        db,
                        owner_user_id=other_id,
                        subject_id=other_subject.id,
                        title="other owner evidence",
                        evidence_kind=EvidenceKind.DOCUMENT,
                        privacy_class=EvidencePrivacyClass.PRIVATE,
                        storage_uri=(
                            f"local-evidence://{other_id}/{uuid.uuid4()}/o.txt"
                        ),
                        content_hash="2" * 64,
                        mime_type="text/plain",
                        size_bytes=2,
                        created_by_actor=actor,
                    )
                    job6 = await create_attachment_scan_job(
                        db, owner_user_id=user_id, evidence_id=evidence_id
                    )
                    # Force reserved job pointing at other owner's evidence id.
                    # Disable FK temporarily is not available; instead create
                    # reserved job for user's evidence then swap evidence_id via
                    # raw SQL (may fail FK). Prefer: reserve then update owner
                    # check by loading other evidence under owner scope → None.
                    await reserve_attachment_scan_job_for_worker(
                        db,
                        job_id=job6.id,
                        owner_user_id=user_id,
                        expected_content_hash_snapshot=content_hash,
                    )
                    # Swap to other owner's evidence (FK allows any evidence_records.id).
                    job6.evidence_id = other_ev.id
                    job6.content_hash_snapshot = "2" * 64
                    await db.commit()
                    foreign = await apply_attachment_scan_worker_result(
                        db,
                        owner_user_id=user_id,
                        scan_job_id=job6.id,
                        expected_content_hash_snapshot="2" * 64,
                        plan=_passed_plan(),
                    )
                    assert foreign.decision is (
                        ScanWorkerResultApplicationDecision.EVIDENCE_NOT_FOUND
                    )

                    # Queue cancellation still works on a reserved job.
                    ev7 = await create_evidence_record(
                        db,
                        owner_user_id=user_id,
                        subject_id=subject_id,
                        title="F29 cancel",
                        evidence_kind=EvidenceKind.DOCUMENT,
                        privacy_class=EvidencePrivacyClass.PRIVATE,
                        storage_uri=(
                            f"local-evidence://{user_id}/{uuid.uuid4()}/c.txt"
                        ),
                        content_hash="3" * 64,
                        mime_type="text/plain",
                        size_bytes=2,
                        created_by_actor=actor,
                    )
                    job7 = await create_attachment_scan_job(
                        db, owner_user_id=user_id, evidence_id=ev7.id
                    )
                    await reserve_attachment_scan_job_for_worker(
                        db,
                        job_id=job7.id,
                        owner_user_id=user_id,
                        expected_content_hash_snapshot="3" * 64,
                    )
                    cancelled = await cancel_attachment_scan_job(
                        db,
                        job_id=job7.id,
                        owner_user_id=user_id,
                        reason="user cancelled",
                    )
                    assert cancelled.job_status == "cancelled"
                    assert cancelled.cancelled_at is not None

                    # F22 public non-worker behaviour still works (reserve+complete).
                    ev8 = await create_evidence_record(
                        db,
                        owner_user_id=user_id,
                        subject_id=subject_id,
                        title="F29 f22 path",
                        evidence_kind=EvidenceKind.DOCUMENT,
                        privacy_class=EvidencePrivacyClass.PRIVATE,
                        storage_uri=(
                            f"local-evidence://{user_id}/{uuid.uuid4()}/f22.txt"
                        ),
                        content_hash="4" * 64,
                        mime_type="text/plain",
                        size_bytes=2,
                        created_by_actor=actor,
                    )
                    job8 = await create_attachment_scan_job(
                        db, owner_user_id=user_id, evidence_id=ev8.id
                    )
                    r8 = await apply_scan_job_update_plan(
                        db,
                        job_id=job8.id,
                        owner_user_id=user_id,
                        plan=build_persistable_scan_job_update_plan(
                            action=ScanWorkerAction.RESERVE_JOB,
                            job_status="reserved",
                            attachment_safety_status="scan_pending",
                        ),
                    )
                    assert r8.job_status == "reserved"
                    c8 = await apply_scan_job_update_plan(
                        db,
                        job_id=job8.id,
                        owner_user_id=user_id,
                        plan=_passed_plan(),
                    )
                    assert c8.job_status == "completed"
                    assert c8.attachment_safety_status == "scan_passed"
            finally:
                await engine.dispose()

        asyncio.run(_run())


@require_disposable_postgres
def test_concurrent_identical_and_conflicting_double_application() -> None:
    with temporary_database(prefix=F29_PREFIX) as (_name, url):
        prepare_database(url)
        assert foundation_heads() == [F0011]
        user_id = _insert_user(url)

        async def _run() -> None:
            engine = create_async_engine(
                _async_url(url), pool_pre_ping=True, pool_size=5
            )
            sessions = async_sessionmaker(
                bind=engine, expire_on_commit=False, class_=AsyncSession
            )
            try:
                async with sessions() as setup:
                    subject = CareerSubject(owner_user_id=user_id)
                    setup.add(subject)
                    await setup.commit()
                    await setup.refresh(subject)
                    subject_id = subject.id
                    actor = ActorRef(
                        actor_type=ActorType.USER, actor_id=new_entity_id()
                    )
                    content_hash = "9" * 64
                    evidence = await create_evidence_record(
                        setup,
                        owner_user_id=user_id,
                        subject_id=subject_id,
                        title="F29 concurrent",
                        evidence_kind=EvidenceKind.DOCUMENT,
                        privacy_class=EvidencePrivacyClass.PRIVATE,
                        storage_uri=(
                            f"local-evidence://{user_id}/{uuid.uuid4()}/x.txt"
                        ),
                        content_hash=content_hash,
                        mime_type="text/plain",
                        size_bytes=3,
                        created_by_actor=actor,
                    )
                    job = await create_attachment_scan_job(
                        setup, owner_user_id=user_id, evidence_id=evidence.id
                    )
                    await reserve_attachment_scan_job_for_worker(
                        setup,
                        job_id=job.id,
                        owner_user_id=user_id,
                        expected_content_hash_snapshot=content_hash,
                    )
                    job_id = job.id
                    await setup.refresh(job)
                    attempt_before = job.attempt_count

                barrier = asyncio.Barrier(2)
                plan = _passed_plan(engine_name="conc", engine_version="1")

                async def _apply_identical() -> ScanWorkerResultApplicationDecision:
                    async with sessions() as db:
                        await barrier.wait()
                        result = await apply_attachment_scan_worker_result(
                            db,
                            owner_user_id=user_id,
                            scan_job_id=job_id,
                            expected_content_hash_snapshot=content_hash,
                            plan=plan,
                        )
                        return result.decision

                d1, d2 = await asyncio.gather(_apply_identical(), _apply_identical())
                decisions = {d1, d2}
                assert ScanWorkerResultApplicationDecision.APPLIED in decisions
                assert decisions <= {
                    ScanWorkerResultApplicationDecision.APPLIED,
                    ScanWorkerResultApplicationDecision.ALREADY_APPLIED,
                }

                async with sessions() as db:
                    row = (
                        await db.execute(
                            select(AttachmentScanJob).where(
                                AttachmentScanJob.id == job_id
                            )
                        )
                    ).scalar_one()
                    assert row.job_status == "completed"
                    assert row.attachment_safety_status == "scan_passed"
                    assert row.engine_name == "conc"
                    assert row.engine_version == "1"
                    assert row.attempt_count == attempt_before
                    assert row.completed_at is not None
                    # No torn / mixed projection.
                    assert row.attachment_safety_status != "scan_failed"
                    assert row.attachment_safety_status != "scan_error"
                    completed_at = row.completed_at
                    updated_at = row.updated_at

                # Exact replay still stable after concurrency.
                async with sessions() as db:
                    again = await apply_attachment_scan_worker_result(
                        db,
                        owner_user_id=user_id,
                        scan_job_id=job_id,
                        expected_content_hash_snapshot=content_hash,
                        plan=plan,
                    )
                    assert again.decision is (
                        ScanWorkerResultApplicationDecision.ALREADY_APPLIED
                    )
                    row2 = (
                        await db.execute(
                            select(AttachmentScanJob).where(
                                AttachmentScanJob.id == job_id
                            )
                        )
                    ).scalar_one()
                    assert row2.completed_at == completed_at
                    assert row2.updated_at == updated_at

                # Conflicting concurrent apply on a fresh reserved job.
                async with sessions() as setup2:
                    ev_b = await create_evidence_record(
                        setup2,
                        owner_user_id=user_id,
                        subject_id=subject_id,
                        title="F29 conflict conc",
                        evidence_kind=EvidenceKind.DOCUMENT,
                        privacy_class=EvidencePrivacyClass.PRIVATE,
                        storage_uri=(
                            f"local-evidence://{user_id}/{uuid.uuid4()}/y.txt"
                        ),
                        content_hash="8" * 64,
                        mime_type="text/plain",
                        size_bytes=3,
                        created_by_actor=actor,
                    )
                    job_b = await create_attachment_scan_job(
                        setup2, owner_user_id=user_id, evidence_id=ev_b.id
                    )
                    await reserve_attachment_scan_job_for_worker(
                        setup2,
                        job_id=job_b.id,
                        owner_user_id=user_id,
                        expected_content_hash_snapshot="8" * 64,
                    )
                    job_b_id = job_b.id

                barrier2 = asyncio.Barrier(2)
                plan_pass = _passed_plan(engine_name="a", engine_version="1")
                plan_fail = _failed_plan(engine_name="b", engine_version="2")

                async def _apply_pass() -> ScanWorkerResultApplicationDecision:
                    async with sessions() as db:
                        await barrier2.wait()
                        r = await apply_attachment_scan_worker_result(
                            db,
                            owner_user_id=user_id,
                            scan_job_id=job_b_id,
                            expected_content_hash_snapshot="8" * 64,
                            plan=plan_pass,
                        )
                        return r.decision

                async def _apply_fail() -> ScanWorkerResultApplicationDecision:
                    async with sessions() as db:
                        await barrier2.wait()
                        r = await apply_attachment_scan_worker_result(
                            db,
                            owner_user_id=user_id,
                            scan_job_id=job_b_id,
                            expected_content_hash_snapshot="8" * 64,
                            plan=plan_fail,
                        )
                        return r.decision

                c1, c2 = await asyncio.gather(_apply_pass(), _apply_fail())
                conflict_set = {c1, c2}
                assert ScanWorkerResultApplicationDecision.APPLIED in conflict_set
                assert (
                    ScanWorkerResultApplicationDecision.CONFLICTING_REPLAY
                    in conflict_set
                    or ScanWorkerResultApplicationDecision.APPLIED in conflict_set
                )
                # Exactly one applied; the other must be conflicting (not both applied).
                assert (
                    conflict_set
                    == {
                        ScanWorkerResultApplicationDecision.APPLIED,
                        ScanWorkerResultApplicationDecision.CONFLICTING_REPLAY,
                    }
                )

                async with sessions() as db:
                    final = (
                        await db.execute(
                            select(AttachmentScanJob).where(
                                AttachmentScanJob.id == job_b_id
                            )
                        )
                    ).scalar_one()
                    # Winner is one coherent terminal projection (not mixed).
                    if final.attachment_safety_status == "scan_passed":
                        assert final.job_status == "completed"
                        assert final.engine_name == "a"
                    else:
                        assert final.job_status == "completed"
                        assert final.attachment_safety_status == "scan_failed"
                        assert final.engine_name == "b"
                    ev_row = (
                        await db.execute(
                            select(EvidenceRecord).where(
                                EvidenceRecord.id == final.evidence_id
                            )
                        )
                    ).scalar_one()
                    assert ev_row.content_hash == "8" * 64
            finally:
                await engine.dispose()

        asyncio.run(_run())
