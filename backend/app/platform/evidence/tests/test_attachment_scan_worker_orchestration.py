"""Scanner worker single-job orchestration guard tests (0053-F31).

Requirement map (evidence maps each required behaviour to a test / parameter):

 1  test_configured_noop_preflight_unavailable_no_db_no_scan
 2  test_configured_noop_preflight_unavailable_no_db_no_scan (BoomSession never opened)
 3  test_unavailable_preflight_leaves_queued_job_unchanged
 4  test_unavailable_preflight_leaves_queued_job_unchanged (attempt_count)
 5  test_unavailable_preflight_leaves_queued_job_unchanged (started_at)
 6  test_configured_noop_preflight_unavailable_no_db_no_scan (F27 not called)
 7  test_configured_noop_preflight_unavailable_no_db_no_scan (scan_attachment not called)
 8  test_configured_noop_preflight_unavailable_no_db_no_scan (F29 not called)
 9  test_adapter_info_exception_fails_safe_before_reservation
10  test_executable_adapter_reserves_and_applies_clean (preflight passes)
11  test_executable_adapter_reserves_and_applies_clean (F27 called → reserved)
12  test_reservation_rejections_skip_adapter (owner not-found)
13  test_reservation_rejections_skip_adapter (hash mismatch)
14  test_reservation_result_carries_authoritative_snapshot
15  test_executable_adapter_reserves_and_applies_clean (adapter receives snapshot)
16  test_public_input_surface_rejects_attachment_metadata
17  test_executable_adapter_reserves_and_applies_clean (reservation session closed)
18  test_executable_adapter_reserves_and_applies_clean (no active session during scan)
19  test_executable_adapter_reserves_and_applies_clean (application uses new session)
20  test_executable_adapter_reserves_and_applies_clean (CLEAN → completed/scan_passed)
21  test_malicious_and_suspicious_persist_scan_failed (malicious)
22  test_malicious_and_suspicious_persist_scan_failed (suspicious)
23  test_terminal_error_verdicts_mark_error (timeout)
24  test_terminal_error_verdicts_mark_error (error)
25  test_terminal_error_verdicts_mark_error (unsupported)
26  test_post_reservation_not_run_becomes_mark_error
27  test_adapter_now_unavailable_becomes_mark_error
28  test_malformed_adapter_return_becomes_mark_error
29  test_adapter_exception_becomes_mark_error
30  test_mapping_exception_becomes_mark_error
31  test_no_fake_clean_on_bad_paths
32  test_no_fabricated_engine_on_bad_paths
33  test_safe_message_redacts_paths
34  test_f29_decision_mapping[applied]
35  test_f29_decision_mapping[already_applied]
36  test_f29_decision_mapping[evidence_not_found] + test_hash_drift_rejection_leaves_reserved
37  test_hash_drift_rejection_leaves_reserved
38  test_f29_decision_mapping[conflicting_replay]
39  test_hash_drift_rejection_leaves_reserved (no auto-cancel) + test_f29_decision_mapping
40  test_module_has_no_forbidden_imports_or_calls (no direct F22 apply)
41  test_process_interrupt_propagates[CancelledError]
42  test_process_interrupt_propagates[KeyboardInterrupt]
43  test_process_interrupt_propagates[SystemExit]
44  test_executable_adapter_reserves_and_applies_clean (evidence unchanged)
45  test_executable_adapter_reserves_and_applies_clean (claim unchanged)
46  test_executable_adapter_reserves_and_applies_clean (review unchanged)
47  test_f26_dry_run_remains_disabled
48  F27 reservation suite (run separately) + test_orchestration_flags_and_summary
49  F29 result-application suite (run separately) + test_orchestration_flags_and_summary
50  test_module_has_no_forbidden_imports_or_calls
51  test_no_worker_loop_or_startup_registration
52  test_no_worker_loop_or_startup_registration
53  test_no_worker_admin_scan_quarantine_audit_routes / test_no_frontend_worker_admin_scan_ui
54  test_no_db_migration_or_scanner_dependency
55  test_concurrent_same_job_only_reserved_calls_invoke_adapter
"""

from __future__ import annotations

import ast
import asyncio
import inspect
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.db.migration_runner import foundation_heads, prepare_database
from app.db.models.attachment_scan import AttachmentScanJob
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
from app.platform.evidence.attachment_scan_worker import (
    ScanResultContract,
    ScannerVerdict,
)
from app.platform.evidence.attachment_scan_worker_dry_run import (
    SCAN_WORKER_DB_MUTATION_ENABLED,
    SCAN_WORKER_DRY_RUN_ENABLED,
    SCAN_WORKER_ENABLED,
    current_scan_worker_dry_run_plan,
)
from app.platform.evidence.attachment_scan_worker_orchestration import (
    SCAN_WORKER_ORCHESTRATION_APPLIES_RESULTS_VIA_F29_ONLY,
    SCAN_WORKER_ORCHESTRATION_GUARD_ENABLED,
    SCAN_WORKER_ORCHESTRATION_READS_FILES,
    SCAN_WORKER_ORCHESTRATION_SESSION_BOUNDARIES,
    ScanWorkerOrchestrationOutcome,
    adapter_is_executable,
    orchestrate_attachment_scan_job,
    orchestration_guard_summary,
)
from app.platform.evidence.attachment_scan_worker_reservation import (
    ReservedJobSnapshot,
    ScanWorkerReservationDecision,
    ScanWorkerReservationResult,
    reservation_guard_summary,
    reserve_attachment_scan_job_for_worker,
)
from app.platform.evidence.attachment_scan_worker_result_application import (
    ScanWorkerResultApplicationDecision,
    ScanWorkerResultApplicationResult,
    result_application_guard_summary,
)
from app.platform.evidence.attachment_scanner_adapter import (
    ScannerAdapterCapability,
    ScannerAdapterInfo,
    ScannerAvailability,
)
from app.platform.evidence.service import (
    create_evidence_record,
    link_evidence_to_claim,
)
from app.platform.identity.refs import ActorRef, ActorType
from app.platform.kernel import new_entity_id
from app.platform.verification.service import create_review_request

REPO_ROOT = Path(__file__).resolve().parents[5]
ORCH_MODULE = (
    REPO_ROOT
    / "backend"
    / "app"
    / "platform"
    / "evidence"
    / "attachment_scan_worker_orchestration.py"
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
# Reuse an approved disposable prefix (do not invent new prefixes).
F31_PREFIX = "ck_f2svc_"
F0011 = "f0011_attachment_scan_queue"


def _async_url(sync_url: str) -> str:
    return sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)


def _insert_user(sync_url: str, *, email_prefix: str = "f31") -> uuid.UUID:
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
                    full_name="F31 User",
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


# --------------------------------------------------------------------------
# Controlled adapters and session tracking (test-only injection seam).
# --------------------------------------------------------------------------


def _clean_result() -> ScanResultContract:
    return ScanResultContract(
        scanner_name="test-exec",
        scanner_version="1",
        verdict=ScannerVerdict.CLEAN,
        duration_ms=1,
        completed_at=datetime.now(timezone.utc),
    )


def _verdict_result(
    verdict: ScannerVerdict,
    *,
    code: str | None = None,
    message: str | None = None,
) -> ScanResultContract:
    return ScanResultContract(
        scanner_name="test-exec",
        scanner_version="1",
        verdict=verdict,
        safe_error_code=code,
        safe_error_message=message,
        duration_ms=1,
        completed_at=datetime.now(timezone.utc),
    )


class _NoopAdapter:
    """Unavailable adapter equivalent to the configured production adapter."""

    def adapter_info(self) -> ScannerAdapterInfo:
        return ScannerAdapterInfo(
            name="noop_unavailable",
            version="0",
            availability=ScannerAvailability.UNAVAILABLE,
            capabilities=(ScannerAdapterCapability.UNAVAILABLE,),
            warning="",
        )

    def scan_attachment(self, **kwargs: object) -> ScanResultContract:
        raise AssertionError("scan_attachment must not be called when unavailable")


class _RaisingInfoAdapter:
    """adapter_info raises an ordinary operational exception."""

    def adapter_info(self) -> ScannerAdapterInfo:
        raise RuntimeError("adapter_info failed at /tmp/secret.bin")

    def scan_attachment(self, **kwargs: object) -> ScanResultContract:
        raise AssertionError("scan_attachment must not be called")


class _ExecAdapter:
    """
    Executable test adapter (passes preflight). scan_attachment returns a
    preset result, or raises a preset exception, and records what it received.
    """

    def __init__(
        self,
        *,
        result: object | None = None,
        exc: BaseException | None = None,
        tracker: "_TrackingSessionFactory | None" = None,
    ) -> None:
        self._result = result
        self._exc = exc
        self._tracker = tracker
        self.invoked = False
        self.received: dict[str, object] | None = None
        self.observed_active_during_scan: int | None = None

    def adapter_info(self) -> ScannerAdapterInfo:
        return ScannerAdapterInfo(
            name="test-exec",
            version="1",
            availability=ScannerAvailability.AVAILABLE,
            capabilities=(ScannerAdapterCapability.MALWARE_SCAN,),
            warning="",
        )

    def scan_attachment(
        self,
        *,
        evidence_id: object | None = None,
        content_hash: str | None = None,
        mime_type: str | None = None,
        size_bytes: int | None = None,
    ) -> object:
        self.invoked = True
        self.received = {
            "evidence_id": evidence_id,
            "content_hash": content_hash,
            "mime_type": mime_type,
            "size_bytes": size_bytes,
        }
        if self._tracker is not None:
            self.observed_active_during_scan = self._tracker.active
        if self._exc is not None:
            raise self._exc
        return self._result


class _TrackingSessionFactory:
    """Wrap a real async session factory to observe open/active boundaries."""

    def __init__(self, real_factory: async_sessionmaker[AsyncSession]) -> None:
        self._real = real_factory
        self.active = 0
        self.opened = 0
        self.max_concurrent = 0
        self.session_ids: list[int] = []

    def __call__(self) -> "_TrackingSessionCtx":
        return _TrackingSessionCtx(self)


class _TrackingSessionCtx:
    def __init__(self, parent: _TrackingSessionFactory) -> None:
        self._parent = parent
        self._cm = parent._real()

    async def __aenter__(self) -> AsyncSession:
        session = await self._cm.__aenter__()
        self._parent.active += 1
        self._parent.opened += 1
        self._parent.max_concurrent = max(
            self._parent.max_concurrent, self._parent.active
        )
        self._parent.session_ids.append(id(session))
        return session

    async def __aexit__(self, *exc: object) -> object:
        self._parent.active -= 1
        return await self._cm.__aexit__(*exc)


# --------------------------------------------------------------------------
# Static / non-DB tests
# --------------------------------------------------------------------------


def test_orchestration_flags_and_summary() -> None:
    assert SCAN_WORKER_ORCHESTRATION_GUARD_ENABLED is True
    assert SCAN_WORKER_ORCHESTRATION_READS_FILES is False
    assert SCAN_WORKER_ORCHESTRATION_APPLIES_RESULTS_VIA_F29_ONLY is True
    assert SCAN_WORKER_ORCHESTRATION_SESSION_BOUNDARIES == 3
    summary = orchestration_guard_summary()
    for key in (
        "runs_worker_loop",
        "polls_queue",
        "selects_jobs",
        "registers_on_startup",
        "reads_files",
        "uses_real_scanner_dependency",
        "exposes_route",
        "calls_public_apply_scan_job_update_plan",
        "forces_terminal_state_on_rejection",
        "auto_cancels",
        "adds_lease_ttl_reclaim",
        "emits_audit",
        "mutates_evidence_record",
        "mutates_claim_record",
        "mutates_review_request",
        "is_scanning",
        "is_verification",
    ):
        assert summary[key] is False, key
    assert summary["applies_results_via_f29_only"] is True
    assert summary["no_active_session_during_adapter"] is True
    # F27 / F29 guards remain importable and unchanged in surface (#48, #49).
    assert reservation_guard_summary()["is_verification"] is False
    assert result_application_guard_summary()["is_verification"] is False


def test_preflight_predicate() -> None:
    def info(avail: ScannerAvailability, caps: tuple) -> ScannerAdapterInfo:
        return ScannerAdapterInfo(
            name="x", version="1", availability=avail, capabilities=caps, warning=""
        )

    # Executable: AVAILABLE + MALWARE_SCAN + no UNAVAILABLE.
    assert adapter_is_executable(
        info(ScannerAvailability.AVAILABLE, (ScannerAdapterCapability.MALWARE_SCAN,))
    )
    # Unavailable availability fails.
    assert not adapter_is_executable(
        info(ScannerAvailability.UNAVAILABLE, (ScannerAdapterCapability.MALWARE_SCAN,))
    )
    # Missing MALWARE_SCAN fails.
    assert not adapter_is_executable(
        info(ScannerAvailability.AVAILABLE, (ScannerAdapterCapability.UNAVAILABLE,))
    )
    # UNAVAILABLE capability present fails even if MALWARE_SCAN present.
    assert not adapter_is_executable(
        info(
            ScannerAvailability.AVAILABLE,
            (
                ScannerAdapterCapability.MALWARE_SCAN,
                ScannerAdapterCapability.UNAVAILABLE,
            ),
        )
    )


def test_public_input_surface_rejects_attachment_metadata() -> None:
    sig = inspect.signature(orchestrate_attachment_scan_job)
    params = set(sig.parameters)
    assert params == {
        "owner_user_id",
        "scan_job_id",
        "expected_content_hash_snapshot",
        "session_factory",
        "adapter_factory",
    }
    for forbidden in (
        "evidence_id",
        "mime_type",
        "size_bytes",
        "storage_uri",
        "storage_path",
        "attachment_bytes",
        "content",
        "snapshot",
        "adapter_name",
    ):
        assert forbidden not in params, forbidden


class _BoomFactory:
    """Session factory that fails loudly if the DB is ever opened."""

    def __call__(self) -> object:
        raise AssertionError("no database session may open on the unavailable path")


def test_configured_noop_preflight_unavailable_no_db_no_scan() -> None:
    async def _run() -> None:
        result = await orchestrate_attachment_scan_job(
            owner_user_id=uuid.uuid4(),
            scan_job_id=uuid.uuid4(),
            expected_content_hash_snapshot="a" * 64,
            session_factory=_BoomFactory(),  # (#2/#6/#8) no F27/F29 → no session
            adapter_factory=_NoopAdapter,  # (#7) scan_attachment asserts if called
        )
        assert result.outcome in (
            ScanWorkerOrchestrationOutcome.SCANNER_UNAVAILABLE,
            ScanWorkerOrchestrationOutcome.SKIPPED_UNAVAILABLE,
        )
        assert result.scanner_executable is False
        assert result.reserved is False
        assert result.reservation_decision is None
        assert result.result_application_decision is None
        # Generic message: reveals nothing about the supplied job.
        assert "/" not in result.safe_message
        assert str(result.job_id) not in result.safe_message

    asyncio.run(_run())


def test_adapter_info_exception_fails_safe_before_reservation() -> None:
    async def _run() -> None:
        result = await orchestrate_attachment_scan_job(
            owner_user_id=uuid.uuid4(),
            scan_job_id=uuid.uuid4(),
            expected_content_hash_snapshot="a" * 64,
            session_factory=_BoomFactory(),
            adapter_factory=_RaisingInfoAdapter,
        )
        assert result.outcome in (
            ScanWorkerOrchestrationOutcome.SCANNER_UNAVAILABLE,
            ScanWorkerOrchestrationOutcome.SKIPPED_UNAVAILABLE,
        )
        assert result.scanner_executable is False
        assert "tmp" not in result.safe_message.lower()
        assert "secret" not in result.safe_message.lower()

    asyncio.run(_run())


def test_f26_dry_run_remains_disabled() -> None:
    assert SCAN_WORKER_ENABLED is False
    assert SCAN_WORKER_DRY_RUN_ENABLED is False
    assert SCAN_WORKER_DB_MUTATION_ENABLED is False
    plan = current_scan_worker_dry_run_plan()
    assert plan.runner_enabled is False
    assert plan.db_mutation_enabled is False


def test_module_has_no_forbidden_imports_or_calls() -> None:
    source = ORCH_MODULE.read_text(encoding="utf-8")
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
        "socket",
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
        "app.platform.evidence.attachment_local_scanner_adapter",
        "app.platform.evidence.attachment_quarantine_audit",
        "app.platform.evidence.attachment_quarantine_storage",
        "app.platform.evidence.storage",
    ):
        assert forbidden not in imports, forbidden
    for needle in (
        "import subprocess",
        "apply_scan_job_update_plan(",  # never call public F22 apply directly
        "cancel_attachment_scan_job(",  # never auto-cancel
        "get_scanner_adapter(",
        "with_for_update",  # locking belongs to F29, not the orchestrator
        "SKIP LOCKED",
        "skip_locked",
        "emit_quarantine",
        "record_quarantine",
        "open(",
        "Path(",
        "read_bytes",
        "BackgroundTasks",
        "asyncio.create_task",
        "while True",
        "def run_worker",
        "def start_worker",
        "def poll",
    ):
        assert needle not in source, needle
    # Applies results only through the F29 guard.
    assert "apply_attachment_scan_worker_result" in source
    # Preflight reads adapter_info only.
    assert "adapter_info(" in source
    assert "scan_attachment(" in source
    # No EvidenceRecord/Claim/Review model names appear.
    names: set[str] = set()
    for node in ast.walk(tree):
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
        "attachment_scan_worker_orchestration",
        "orchestrate_attachment_scan_job",
        "register_scan_worker",
        "start_scan_worker",
    ):
        assert needle not in main_src, needle
    source = ORCH_MODULE.read_text(encoding="utf-8")
    assert "while True" not in source
    assert "def run_worker" not in source
    assert "def start_worker" not in source
    assert "get_latest_attachment_scan_job" not in source
    assert "list_attachment_scan_jobs_for_owner" not in source


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
                "/orchestrate",
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
            "orchestrate scan",
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


# --------------------------------------------------------------------------
# F29 decision mapping (no DB; reservation and F29 patched at the seam).
# --------------------------------------------------------------------------


class _NullSession:
    async def __aenter__(self) -> "_NullSession":
        return self

    async def __aexit__(self, *exc: object) -> bool:
        return False


def _null_factory() -> _NullSession:
    return _NullSession()


def _reserved_result(job_id: uuid.UUID, owner_id: uuid.UUID) -> ScanWorkerReservationResult:
    snapshot = ReservedJobSnapshot(
        job_id=job_id,
        owner_user_id=owner_id,
        evidence_id=uuid.uuid4(),
        content_hash_snapshot="a" * 64,
        mime_type_snapshot="text/plain",
        size_bytes_snapshot=4,
    )
    return ScanWorkerReservationResult(
        reserved=True,
        decision=ScanWorkerReservationDecision.RESERVED,
        job_id=job_id,
        owner_user_id=owner_id,
        previous_status="queued",
        new_status="reserved",
        attempt_count=1,
        safe_message="reserved",
        snapshot=snapshot,
    )


def _f29_result(
    decision: ScanWorkerResultApplicationDecision,
    job_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> ScanWorkerResultApplicationResult:
    return ScanWorkerResultApplicationResult(
        applied=decision is ScanWorkerResultApplicationDecision.APPLIED,
        decision=decision,
        job_id=job_id,
        owner_user_id=owner_id,
        previous_status="reserved",
        new_status="completed"
        if decision is ScanWorkerResultApplicationDecision.APPLIED
        else "reserved",
        attempt_count=1,
        completed_at=None,
        safe_message="f29",
    )


@pytest.mark.parametrize(
    "decision,expected_outcome,expected_reserved",
    [
        (
            ScanWorkerResultApplicationDecision.APPLIED,
            ScanWorkerOrchestrationOutcome.APPLIED,
            False,
        ),
        (
            ScanWorkerResultApplicationDecision.ALREADY_APPLIED,
            ScanWorkerOrchestrationOutcome.ALREADY_APPLIED,
            False,
        ),
        (
            ScanWorkerResultApplicationDecision.EVIDENCE_NOT_FOUND,
            ScanWorkerOrchestrationOutcome.RESULT_APPLICATION_REJECTED,
            True,
        ),
        (
            ScanWorkerResultApplicationDecision.HASH_MISMATCH,
            ScanWorkerOrchestrationOutcome.RESULT_APPLICATION_REJECTED,
            True,
        ),
        (
            ScanWorkerResultApplicationDecision.CONFLICTING_REPLAY,
            ScanWorkerOrchestrationOutcome.RESULT_APPLICATION_REJECTED,
            True,
        ),
        (
            ScanWorkerResultApplicationDecision.NOT_RESERVED,
            ScanWorkerOrchestrationOutcome.RESULT_APPLICATION_REJECTED,
            True,
        ),
        (
            ScanWorkerResultApplicationDecision.ACTION_NOT_ALLOWED,
            ScanWorkerOrchestrationOutcome.RESULT_APPLICATION_REJECTED,
            True,
        ),
        (
            ScanWorkerResultApplicationDecision.PLAN_NOT_PERSISTABLE,
            ScanWorkerOrchestrationOutcome.RESULT_APPLICATION_REJECTED,
            True,
        ),
    ],
)
def test_f29_decision_mapping(
    decision: ScanWorkerResultApplicationDecision,
    expected_outcome: ScanWorkerOrchestrationOutcome,
    expected_reserved: bool,
) -> None:
    job_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    adapter = _ExecAdapter(result=_clean_result())

    async def _run() -> None:
        with (
            patch(
                "app.platform.evidence.attachment_scan_worker_orchestration"
                ".reserve_attachment_scan_job_for_worker",
                new_callable=AsyncMock,
                return_value=_reserved_result(job_id, owner_id),
            ),
            patch(
                "app.platform.evidence.attachment_scan_worker_orchestration"
                ".apply_attachment_scan_worker_result",
                new_callable=AsyncMock,
                return_value=_f29_result(decision, job_id, owner_id),
            ) as mock_apply,
        ):
            result = await orchestrate_attachment_scan_job(
                owner_user_id=owner_id,
                scan_job_id=job_id,
                expected_content_hash_snapshot="a" * 64,
                session_factory=_null_factory,
                adapter_factory=lambda: adapter,
            )
        assert result.outcome is expected_outcome
        assert result.reserved is expected_reserved
        assert result.result_application_decision == decision.value
        # F29 is the only application path, called exactly once.
        assert mock_apply.await_count == 1
        # The adapter ran (reservation succeeded at the seam).
        assert adapter.invoked is True

    asyncio.run(_run())


# --------------------------------------------------------------------------
# DB-backed integration tests (require disposable PostgreSQL).
# --------------------------------------------------------------------------


async def _seed_queued_job(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    subject_id: uuid.UUID,
    actor: ActorRef,
    content_hash: str,
    title: str,
    size_bytes: int = 4,
) -> tuple[object, AttachmentScanJob]:
    evidence = await create_evidence_record(
        db,
        owner_user_id=user_id,
        subject_id=subject_id,
        title=title,
        evidence_kind=EvidenceKind.DOCUMENT,
        privacy_class=EvidencePrivacyClass.PRIVATE,
        storage_uri=f"local-evidence://{user_id}/{uuid.uuid4()}/n.txt",
        content_hash=content_hash,
        mime_type="text/plain",
        size_bytes=size_bytes,
        created_by_actor=actor,
    )
    job = await create_attachment_scan_job(
        db, owner_user_id=user_id, evidence_id=evidence.id
    )
    return evidence, job


@require_disposable_postgres
def test_executable_adapter_reserves_and_applies_clean() -> None:
    with temporary_database(prefix=F31_PREFIX) as (_name, url):
        prepare_database(url)
        assert foundation_heads() == [F0011]
        user_id = _insert_user(url)

        async def _run() -> None:
            engine = create_async_engine(_async_url(url), pool_pre_ping=True)
            real_sessions = async_sessionmaker(
                bind=engine, expire_on_commit=False, class_=AsyncSession
            )
            tracker = _TrackingSessionFactory(real_sessions)
            try:
                async with real_sessions() as setup:
                    subject = CareerSubject(owner_user_id=user_id)
                    setup.add(subject)
                    await setup.commit()
                    await setup.refresh(subject)
                    actor = ActorRef(
                        actor_type=ActorType.USER, actor_id=new_entity_id()
                    )
                    content_hash = "a" * 64
                    evidence, job = await _seed_queued_job(
                        setup,
                        user_id=user_id,
                        subject_id=subject.id,
                        actor=actor,
                        content_hash=content_hash,
                        title="F31 clean",
                    )
                    claim = await create_claim(
                        setup,
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
                        setup,
                        claim_id=claim.id,
                        evidence_id=evidence.id,
                        link_role=ClaimEvidenceLinkRole.SUPPORTS,
                        created_by_actor=actor,
                    )
                    review = await create_review_request(
                        setup,
                        owner_user_id=user_id,
                        claim_id=claim.id,
                        created_by_actor=actor,
                    )
                    job_id = job.id
                    evidence_id = evidence.id
                    prior_support = claim.support_status
                    prior_verification = claim.verification_status
                    prior_review = review.review_state
                    prior_hash = evidence.content_hash
                    prior_uri = evidence.storage_uri

                adapter = _ExecAdapter(result=_clean_result(), tracker=tracker)
                result = await orchestrate_attachment_scan_job(
                    owner_user_id=user_id,
                    scan_job_id=job_id,
                    expected_content_hash_snapshot=content_hash,
                    session_factory=tracker,
                    adapter_factory=lambda: adapter,
                )

                # (#10/#11/#20) preflight passed, reserved, applied clean.
                assert result.outcome is ScanWorkerOrchestrationOutcome.APPLIED
                assert result.scanner_executable is True
                assert result.reservation_decision == "reserved"
                assert result.result_application_decision == "applied"
                # (#15) adapter received authoritative reserved-row values only.
                assert adapter.invoked is True
                assert adapter.received == {
                    "evidence_id": evidence_id,
                    "content_hash": content_hash,
                    "mime_type": "text/plain",
                    "size_bytes": 4,
                }
                # (#17/#18) no active session while the adapter ran.
                assert adapter.observed_active_during_scan == 0
                # (#19) two distinct short-lived sessions (reserve + apply).
                assert tracker.opened == 2
                assert tracker.max_concurrent == 1
                assert len(set(tracker.session_ids)) == 2

                async with real_sessions() as check:
                    row = (
                        await check.execute(
                            select(AttachmentScanJob).where(
                                AttachmentScanJob.id == job_id
                            )
                        )
                    ).scalar_one()
                    assert row.job_status == "completed"
                    assert row.attachment_safety_status == "scan_passed"
                    assert row.engine_name == "test-exec"
                    assert row.attempt_count == 1
                    assert row.completed_at is not None
                    # (#44/#45/#46) no evidence / claim / review mutation.
                    ev = (
                        await check.execute(
                            select(type(evidence)).where(type(evidence).id == evidence_id)
                        )
                    ).scalar_one()
                    assert ev.content_hash == prior_hash
                    assert ev.storage_uri == prior_uri
                    c = (
                        await check.execute(
                            select(type(claim)).where(type(claim).id == claim.id)
                        )
                    ).scalar_one()
                    assert c.support_status == prior_support
                    assert c.verification_status == prior_verification
                    r = (
                        await check.execute(
                            select(type(review)).where(type(review).id == review.id)
                        )
                    ).scalar_one()
                    assert r.review_state == prior_review
            finally:
                await engine.dispose()

        asyncio.run(_run())


@require_disposable_postgres
def test_unavailable_preflight_leaves_queued_job_unchanged() -> None:
    with temporary_database(prefix=F31_PREFIX) as (_name, url):
        prepare_database(url)
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
                    content_hash = "b" * 64
                    _evidence, job = await _seed_queued_job(
                        db,
                        user_id=user_id,
                        subject_id=subject.id,
                        actor=actor,
                        content_hash=content_hash,
                        title="F31 noop unchanged",
                    )
                    job_id = job.id

                # Real configured adapter (noop/unavailable) → leaves job queued.
                result = await orchestrate_attachment_scan_job(
                    owner_user_id=user_id,
                    scan_job_id=job_id,
                    expected_content_hash_snapshot=content_hash,
                    session_factory=sessions,
                )
                assert result.outcome in (
                    ScanWorkerOrchestrationOutcome.SCANNER_UNAVAILABLE,
                    ScanWorkerOrchestrationOutcome.SKIPPED_UNAVAILABLE,
                )

                async with sessions() as check:
                    row = (
                        await check.execute(
                            select(AttachmentScanJob).where(
                                AttachmentScanJob.id == job_id
                            )
                        )
                    ).scalar_one()
                    assert row.job_status == "queued"  # (#3)
                    assert row.attempt_count == 0  # (#4)
                    assert row.started_at is None  # (#5)
                    assert row.completed_at is None
                    assert (
                        row.attachment_safety_status
                        == AttachmentSafetyStatus.SCAN_PENDING.value
                    )
                    assert row.engine_name is None
                    assert row.safe_error_code is None  # no scan_error created
            finally:
                await engine.dispose()

        asyncio.run(_run())


@require_disposable_postgres
def test_reservation_result_carries_authoritative_snapshot() -> None:
    with temporary_database(prefix=F31_PREFIX) as (_name, url):
        prepare_database(url)
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
                    content_hash = "c" * 64
                    evidence, job = await _seed_queued_job(
                        db,
                        user_id=user_id,
                        subject_id=subject.id,
                        actor=actor,
                        content_hash=content_hash,
                        title="F31 snapshot",
                        size_bytes=7,
                    )
                    reserved = await reserve_attachment_scan_job_for_worker(
                        db,
                        job_id=job.id,
                        owner_user_id=user_id,
                        expected_content_hash_snapshot=content_hash,
                    )
                    assert reserved.decision is ScanWorkerReservationDecision.RESERVED
                    snap = reserved.snapshot
                    assert snap is not None
                    assert snap.job_id == job.id
                    assert snap.owner_user_id == user_id
                    assert snap.evidence_id == evidence.id
                    assert snap.content_hash_snapshot == content_hash
                    assert snap.mime_type_snapshot == "text/plain"
                    assert snap.size_bytes_snapshot == 7
            finally:
                await engine.dispose()

        asyncio.run(_run())


@require_disposable_postgres
def test_reservation_rejections_skip_adapter() -> None:
    with temporary_database(prefix=F31_PREFIX) as (_name, url):
        prepare_database(url)
        user_id = _insert_user(url)
        other_id = _insert_user(url, email_prefix="f31other")

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
                    _evidence, job = await _seed_queued_job(
                        db,
                        user_id=user_id,
                        subject_id=subject.id,
                        actor=actor,
                        content_hash=content_hash,
                        title="F31 reject",
                    )
                    job_id = job.id

                # (#12) other owner → safe not_found, adapter not invoked.
                adapter1 = _ExecAdapter(result=_clean_result())
                r1 = await orchestrate_attachment_scan_job(
                    owner_user_id=other_id,
                    scan_job_id=job_id,
                    expected_content_hash_snapshot=content_hash,
                    session_factory=sessions,
                    adapter_factory=lambda: adapter1,
                )
                assert r1.outcome is (
                    ScanWorkerOrchestrationOutcome.RESERVATION_REJECTED
                )
                assert r1.reservation_decision == "not_found"
                assert adapter1.invoked is False

                # (#13) expected-hash mismatch → adapter not invoked.
                adapter2 = _ExecAdapter(result=_clean_result())
                r2 = await orchestrate_attachment_scan_job(
                    owner_user_id=user_id,
                    scan_job_id=job_id,
                    expected_content_hash_snapshot="e" * 64,
                    session_factory=sessions,
                    adapter_factory=lambda: adapter2,
                )
                assert r2.outcome is (
                    ScanWorkerOrchestrationOutcome.RESERVATION_REJECTED
                )
                assert r2.reservation_decision == "hash_mismatch"
                assert adapter2.invoked is False

                async with sessions() as check:
                    row = (
                        await check.execute(
                            select(AttachmentScanJob).where(
                                AttachmentScanJob.id == job_id
                            )
                        )
                    ).scalar_one()
                    assert row.job_status == "queued"
                    assert row.attempt_count == 0
            finally:
                await engine.dispose()

        asyncio.run(_run())


def _run_single_verdict(
    url: str,
    user_id: uuid.UUID,
    *,
    title: str,
    content_hash: str,
    adapter_result: object | None = None,
    adapter_exc: BaseException | None = None,
) -> AttachmentScanJob:
    """Reserve+execute+apply one job with a controlled adapter; return final row."""

    async def _run() -> AttachmentScanJob:
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
                actor = ActorRef(actor_type=ActorType.USER, actor_id=new_entity_id())
                _evidence, job = await _seed_queued_job(
                    db,
                    user_id=user_id,
                    subject_id=subject.id,
                    actor=actor,
                    content_hash=content_hash,
                    title=title,
                )
                job_id = job.id

            adapter = _ExecAdapter(result=adapter_result, exc=adapter_exc)
            await orchestrate_attachment_scan_job(
                owner_user_id=user_id,
                scan_job_id=job_id,
                expected_content_hash_snapshot=content_hash,
                session_factory=sessions,
                adapter_factory=lambda: adapter,
            )
            async with sessions() as check:
                return (
                    await check.execute(
                        select(AttachmentScanJob).where(AttachmentScanJob.id == job_id)
                    )
                ).scalar_one()
        finally:
            await engine.dispose()

    return asyncio.run(_run())


@require_disposable_postgres
@pytest.mark.parametrize("verdict", [ScannerVerdict.MALICIOUS, ScannerVerdict.SUSPICIOUS])
def test_malicious_and_suspicious_persist_scan_failed(verdict: ScannerVerdict) -> None:
    with temporary_database(prefix=F31_PREFIX) as (_name, url):
        prepare_database(url)
        user_id = _insert_user(url)
        row = _run_single_verdict(
            url,
            user_id,
            title=f"F31 {verdict.value}",
            content_hash=uuid.uuid4().hex + uuid.uuid4().hex[:32],
            adapter_result=_verdict_result(verdict),
        )
        assert row.job_status == "completed"
        assert row.attachment_safety_status == "scan_failed"
        assert row.attachment_safety_status != "quarantined"


@require_disposable_postgres
@pytest.mark.parametrize(
    "verdict,code",
    [
        (ScannerVerdict.TIMEOUT, "scanner_timeout"),
        (ScannerVerdict.ERROR, "scanner_error"),
        (ScannerVerdict.UNSUPPORTED, "scanner_unsupported"),
    ],
)
def test_terminal_error_verdicts_mark_error(verdict: ScannerVerdict, code: str) -> None:
    with temporary_database(prefix=F31_PREFIX) as (_name, url):
        prepare_database(url)
        user_id = _insert_user(url)
        row = _run_single_verdict(
            url,
            user_id,
            title=f"F31 {verdict.value}",
            content_hash=uuid.uuid4().hex + uuid.uuid4().hex[:32],
            adapter_result=_verdict_result(verdict, code=code, message="engine reported"),
        )
        assert row.job_status == "failed"
        assert row.attachment_safety_status == "scan_error"
        assert row.attachment_safety_status != "scan_passed"
        assert row.safe_error_code == code


@require_disposable_postgres
def test_post_reservation_not_run_becomes_mark_error() -> None:
    with temporary_database(prefix=F31_PREFIX) as (_name, url):
        prepare_database(url)
        user_id = _insert_user(url)
        row = _run_single_verdict(
            url,
            user_id,
            title="F31 not_run",
            content_hash=uuid.uuid4().hex + uuid.uuid4().hex[:32],
            adapter_result=_verdict_result(
                ScannerVerdict.NOT_RUN, code="scanner_unavailable"
            ),
        )
        assert row.job_status == "failed"
        assert row.attachment_safety_status == "scan_error"
        assert row.attachment_safety_status != "scan_passed"
        assert row.engine_name is None  # (#32) no fabricated engine identity


@require_disposable_postgres
def test_adapter_now_unavailable_becomes_mark_error() -> None:
    with temporary_database(prefix=F31_PREFIX) as (_name, url):
        prepare_database(url)
        user_id = _insert_user(url)
        # Adapter passes preflight but then returns NOT_RUN/unavailable.
        row = _run_single_verdict(
            url,
            user_id,
            title="F31 now unavailable",
            content_hash=uuid.uuid4().hex + uuid.uuid4().hex[:32],
            adapter_result=_verdict_result(
                ScannerVerdict.NOT_RUN,
                code="scanner_unavailable",
                message="scanner became unavailable",
            ),
        )
        assert row.job_status == "failed"
        assert row.attachment_safety_status == "scan_error"
        assert row.safe_error_code in {"scanner_unavailable", "scanner_output_unavailable"}
        assert row.engine_name is None


@require_disposable_postgres
def test_malformed_adapter_return_becomes_mark_error() -> None:
    with temporary_database(prefix=F31_PREFIX) as (_name, url):
        prepare_database(url)
        user_id = _insert_user(url)
        row = _run_single_verdict(
            url,
            user_id,
            title="F31 malformed",
            content_hash=uuid.uuid4().hex + uuid.uuid4().hex[:32],
            adapter_result={"not": "a contract"},  # malformed return type
        )
        assert row.job_status == "failed"
        assert row.attachment_safety_status == "scan_error"
        assert row.safe_error_code == "scanner_output_unavailable"
        assert row.engine_name is None


@require_disposable_postgres
def test_adapter_exception_becomes_mark_error() -> None:
    with temporary_database(prefix=F31_PREFIX) as (_name, url):
        prepare_database(url)
        user_id = _insert_user(url)
        row = _run_single_verdict(
            url,
            user_id,
            title="F31 adapter exc",
            content_hash=uuid.uuid4().hex + uuid.uuid4().hex[:32],
            adapter_exc=ValueError("boom at /tmp/secret.bin"),
        )
        assert row.job_status == "failed"
        assert row.attachment_safety_status == "scan_error"
        assert row.engine_name is None
        # (#33) path never leaks into the safe message.
        assert "tmp" not in (row.safe_error_message or "").lower()


@require_disposable_postgres
def test_mapping_exception_becomes_mark_error() -> None:
    with temporary_database(prefix=F31_PREFIX) as (_name, url):
        prepare_database(url)
        user_id = _insert_user(url)
        # A contract whose verdict cannot be mapped raises inside the mapper.
        bad = ScanResultContract(
            scanner_name="test-exec",
            scanner_version="1",
            verdict="not_a_real_verdict",  # type: ignore[arg-type]
            duration_ms=1,
            completed_at=datetime.now(timezone.utc),
        )
        row = _run_single_verdict(
            url,
            user_id,
            title="F31 mapping exc",
            content_hash=uuid.uuid4().hex + uuid.uuid4().hex[:32],
            adapter_result=bad,
        )
        assert row.job_status == "failed"
        assert row.attachment_safety_status == "scan_error"
        assert row.safe_error_code == "scanner_output_unavailable"
        assert row.engine_name is None


@require_disposable_postgres
def test_no_fake_clean_on_bad_paths() -> None:
    with temporary_database(prefix=F31_PREFIX) as (_name, url):
        prepare_database(url)
        user_id = _insert_user(url)
        for title, kwargs in (
            ("nr", {"adapter_result": _verdict_result(ScannerVerdict.NOT_RUN)}),
            ("mal", {"adapter_result": {"bad": 1}}),
            ("exc", {"adapter_exc": RuntimeError("x")}),
        ):
            row = _run_single_verdict(
                url,
                user_id,
                title=f"F31 nofake {title}",
                content_hash=uuid.uuid4().hex + uuid.uuid4().hex[:32],
                **kwargs,
            )
            assert row.attachment_safety_status != "scan_passed"  # (#31)
            assert row.job_status != "completed"
            assert row.engine_name is None  # (#32)


@require_disposable_postgres
def test_no_fabricated_engine_on_bad_paths() -> None:
    with temporary_database(prefix=F31_PREFIX) as (_name, url):
        prepare_database(url)
        user_id = _insert_user(url)
        row = _run_single_verdict(
            url,
            user_id,
            title="F31 engine none",
            content_hash=uuid.uuid4().hex + uuid.uuid4().hex[:32],
            adapter_exc=RuntimeError("no engine"),
        )
        assert row.engine_name is None
        assert row.engine_version is None


@require_disposable_postgres
def test_safe_message_redacts_paths() -> None:
    with temporary_database(prefix=F31_PREFIX) as (_name, url):
        prepare_database(url)
        user_id = _insert_user(url)
        row = _run_single_verdict(
            url,
            user_id,
            title="F31 redact",
            content_hash=uuid.uuid4().hex + uuid.uuid4().hex[:32],
            adapter_result=_verdict_result(
                ScannerVerdict.ERROR,
                code="scanner_error",
                message="failed reading /tmp/secret.bin local-evidence://x/y",
            ),
        )
        msg = (row.safe_error_message or "").lower()
        assert "tmp" not in msg
        assert "local-evidence" not in msg


@require_disposable_postgres
def test_hash_drift_rejection_leaves_reserved() -> None:
    with temporary_database(prefix=F31_PREFIX) as (_name, url):
        prepare_database(url)
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
                    content_hash = "a" * 64
                    evidence, job = await _seed_queued_job(
                        db,
                        user_id=user_id,
                        subject_id=subject.id,
                        actor=actor,
                        content_hash=content_hash,
                        title="F31 drift",
                    )
                    job_id = job.id
                    evidence_id = evidence.id
                    # Simulate live evidence hash drift after enqueue: the job
                    # snapshot still equals expected (reservation succeeds), but
                    # F29's triple-hash guard will reject at apply time.
                    evidence.content_hash = "c" * 64
                    await db.commit()

                adapter = _ExecAdapter(result=_clean_result())
                result = await orchestrate_attachment_scan_job(
                    owner_user_id=user_id,
                    scan_job_id=job_id,
                    expected_content_hash_snapshot=content_hash,
                    session_factory=sessions,
                    adapter_factory=lambda: adapter,
                )
                # (#36/#37) F29 hash-drift rejection surfaces as rejected.
                assert result.outcome is (
                    ScanWorkerOrchestrationOutcome.RESULT_APPLICATION_REJECTED
                )
                assert result.result_application_decision == "hash_mismatch"
                assert result.reserved is True
                assert adapter.invoked is True

                async with sessions() as check:
                    row = (
                        await check.execute(
                            select(AttachmentScanJob).where(
                                AttachmentScanJob.id == job_id
                            )
                        )
                    ).scalar_one()
                    # (#39) not auto-cancelled / not forced terminal.
                    assert row.job_status == "reserved"
                    assert row.cancelled_at is None
                    assert row.completed_at is None
                    assert row.attempt_count == 1
                    ev = (
                        await check.execute(
                            select(type(evidence)).where(type(evidence).id == evidence_id)
                        )
                    ).scalar_one()
                    # Evidence untouched by orchestration (drift set by test only).
                    assert ev.content_hash == "c" * 64
            finally:
                await engine.dispose()

        asyncio.run(_run())


@require_disposable_postgres
@pytest.mark.parametrize(
    "interrupt",
    [asyncio.CancelledError, KeyboardInterrupt, SystemExit],
)
def test_process_interrupt_propagates(interrupt: type[BaseException]) -> None:
    with temporary_database(prefix=F31_PREFIX) as (_name, url):
        prepare_database(url)
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
                    content_hash = uuid.uuid4().hex + uuid.uuid4().hex[:32]
                    _evidence, job = await _seed_queued_job(
                        db,
                        user_id=user_id,
                        subject_id=subject.id,
                        actor=actor,
                        content_hash=content_hash,
                        title="F31 interrupt",
                    )
                    job_id = job.id

                adapter = _ExecAdapter(exc=interrupt())
                with pytest.raises(interrupt):
                    await orchestrate_attachment_scan_job(
                        owner_user_id=user_id,
                        scan_job_id=job_id,
                        expected_content_hash_snapshot=content_hash,
                        session_factory=sessions,
                        adapter_factory=lambda: adapter,
                    )
                assert adapter.invoked is True

                # Interruption after reservation leaves the job reserved (watch item).
                async with sessions() as check:
                    row = (
                        await check.execute(
                            select(AttachmentScanJob).where(
                                AttachmentScanJob.id == job_id
                            )
                        )
                    ).scalar_one()
                    assert row.job_status == "reserved"
                    assert row.attempt_count == 1
                    assert row.completed_at is None
                    assert row.cancelled_at is None
            finally:
                await engine.dispose()

        asyncio.run(_run())


@require_disposable_postgres
def test_concurrent_same_job_only_reserved_calls_invoke_adapter() -> None:
    with temporary_database(prefix=F31_PREFIX) as (_name, url):
        prepare_database(url)
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
                    actor = ActorRef(
                        actor_type=ActorType.USER, actor_id=new_entity_id()
                    )
                    content_hash = "9" * 64
                    _evidence, job = await _seed_queued_job(
                        setup,
                        user_id=user_id,
                        subject_id=subject.id,
                        actor=actor,
                        content_hash=content_hash,
                        title="F31 concurrent",
                        size_bytes=3,
                    )
                    job_id = job.id

                barrier = asyncio.Barrier(2)
                adapters: list[_ExecAdapter] = [
                    _ExecAdapter(result=_clean_result()),
                    _ExecAdapter(result=_clean_result()),
                ]

                async def _call(idx: int):
                    await barrier.wait()
                    return await orchestrate_attachment_scan_job(
                        owner_user_id=user_id,
                        scan_job_id=job_id,
                        expected_content_hash_snapshot=content_hash,
                        session_factory=sessions,  # independent session per call
                        adapter_factory=lambda: adapters[idx],
                    )

                results = await asyncio.gather(_call(0), _call(1))

                # The adapter runs only for a call whose reservation succeeded.
                for result, adapter in zip(results, adapters):
                    if adapter.invoked:
                        assert result.reservation_decision == "reserved"

                outcomes = {r.outcome for r in results}
                assert ScanWorkerOrchestrationOutcome.APPLIED in outcomes
                assert outcomes <= {
                    ScanWorkerOrchestrationOutcome.APPLIED,
                    ScanWorkerOrchestrationOutcome.ALREADY_APPLIED,
                    ScanWorkerOrchestrationOutcome.RESULT_APPLICATION_REJECTED,
                    ScanWorkerOrchestrationOutcome.RESERVATION_REJECTED,
                }

                # Final job state is one coherent terminal projection.
                async with sessions() as check:
                    row = (
                        await check.execute(
                            select(AttachmentScanJob).where(
                                AttachmentScanJob.id == job_id
                            )
                        )
                    ).scalar_one()
                    assert row.job_status == "completed"
                    assert row.attachment_safety_status == "scan_passed"
                    assert row.attachment_safety_status not in {
                        "scan_failed",
                        "scan_error",
                    }
                    # attempt_count is never inflated past a single reservation.
                    assert row.attempt_count == 1
            finally:
                await engine.dispose()

        asyncio.run(_run())
