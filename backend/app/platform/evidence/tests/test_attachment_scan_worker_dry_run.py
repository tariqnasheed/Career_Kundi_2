"""Scanner worker dry-run planning + disabled runner tests (0053-F26)."""

from __future__ import annotations

import ast
from pathlib import Path

from app.main import app
from app.platform.evidence.attachment_scan_worker_dry_run import (
    SCAN_WORKER_AUDIT_EMIT_ENABLED,
    SCAN_WORKER_BACKGROUND_LOOP_ENABLED,
    SCAN_WORKER_DB_MUTATION_ENABLED,
    SCAN_WORKER_DRY_RUN_ENABLED,
    SCAN_WORKER_ENABLED,
    SCAN_WORKER_FILE_ACCESS_ENABLED,
    SCAN_WORKER_SCANNER_EXECUTION_ENABLED,
    SCAN_WORKER_STARTUP_REGISTRATION_ENABLED,
    ScanWorkerDryRunDecision,
    ScanWorkerRunnerMode,
    assert_scan_worker_runner_disabled,
    build_scan_worker_dry_run_decision,
    current_scan_worker_dry_run_plan,
    scan_worker_dry_run_summary,
    scan_worker_dry_run_warning,
    scan_worker_is_enabled,
)

REPO_ROOT = Path(__file__).resolve().parents[5]
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
FRONTEND_PAGES = [
    REPO_ROOT / "frontend" / "src" / "pages" / "EvidenceLibraryPage.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "passport"
    / "PassportEvidencePanel.tsx",
]


def test_worker_flags_are_disabled() -> None:
    assert SCAN_WORKER_ENABLED is False
    assert SCAN_WORKER_DRY_RUN_ENABLED is False
    assert SCAN_WORKER_BACKGROUND_LOOP_ENABLED is False
    assert SCAN_WORKER_STARTUP_REGISTRATION_ENABLED is False
    assert SCAN_WORKER_DB_MUTATION_ENABLED is False
    assert SCAN_WORKER_FILE_ACCESS_ENABLED is False
    assert SCAN_WORKER_SCANNER_EXECUTION_ENABLED is False
    assert SCAN_WORKER_AUDIT_EMIT_ENABLED is False
    assert scan_worker_is_enabled() is False


def test_plan_mode_and_warning() -> None:
    plan = current_scan_worker_dry_run_plan()
    assert plan.runner_enabled is False
    assert plan.dry_run_enabled is False
    assert plan.background_loop_enabled is False
    assert plan.startup_registration_enabled is False
    assert plan.db_mutation_enabled is False
    assert plan.file_access_enabled is False
    assert plan.scanner_execution_enabled is False
    assert plan.audit_emit_enabled is False
    assert plan.mode is ScanWorkerRunnerMode.DISABLED
    assert plan.decision is ScanWorkerDryRunDecision.DISABLED
    warning = scan_worker_dry_run_warning().lower()
    assert "planned but not active" in warning
    assert "worker execution" in warning


def test_dry_run_decisions_are_object_only() -> None:
    assert (
        build_scan_worker_dry_run_decision()
        is ScanWorkerDryRunDecision.DISABLED
    )
    assert (
        build_scan_worker_dry_run_decision(scanner_available=False)
        is ScanWorkerDryRunDecision.WOULD_SKIP_SCANNER_UNAVAILABLE
    )
    assert (
        build_scan_worker_dry_run_decision(plan_persistable=False)
        is ScanWorkerDryRunDecision.WOULD_REJECT_UNPERSISTABLE_PLAN
    )
    assert (
        build_scan_worker_dry_run_decision(hash_matches=False)
        is ScanWorkerDryRunDecision.WOULD_SKIP_HASH_MISMATCH
    )
    assert (
        build_scan_worker_dry_run_decision(job_status="queued")
        is ScanWorkerDryRunDecision.WOULD_RESERVE_JOB
    )
    assert (
        build_scan_worker_dry_run_decision(job_status="completed")
        is ScanWorkerDryRunDecision.WOULD_SKIP_NON_PENDING_JOB
    )
    assert (
        build_scan_worker_dry_run_decision(job_available=False)
        is ScanWorkerDryRunDecision.NO_JOB_AVAILABLE
    )
    # Decisions do not enable runner powers.
    assert_scan_worker_runner_disabled()


def test_assert_disabled_does_not_create_artifacts() -> None:
    assert_scan_worker_runner_disabled()
    assert not (ROUTES / "scan_worker.py").exists()
    assert not (ROUTES / "admin_scan.py").exists()
    assert not (EVIDENCE_PKG / "quarantine.py").exists()


def test_module_has_no_forbidden_imports_or_calls() -> None:
    source = DRY_RUN_MODULE.read_text(encoding="utf-8")
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
        "asyncio",
        "celery",
        "apscheduler",
        "sqlalchemy",
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
        "open(",
        "Path(",
        "read_bytes",
        "BackgroundTasks",
        "asyncio.create_task",
        "AsyncSession",
        "session.commit",
        "EvidenceRecord",
        "ClaimRecord",
        "ReviewRequest",
    ):
        assert needle not in source, needle


def test_no_worker_loop_or_startup_registration() -> None:
    main_src = MAIN_PY.read_text(encoding="utf-8")
    for needle in (
        "attachment_scan_worker_dry_run",
        "attachment_scan_worker",
        "SCAN_WORKER",
        "register_scan_worker",
        "start_scan_worker",
        "scan_worker_dry_run",
    ):
        assert needle not in main_src, needle
    dry = DRY_RUN_MODULE.read_text(encoding="utf-8")
    assert "while True" not in dry
    assert "def run_worker" not in dry
    assert "def start_worker" not in dry
    summary = scan_worker_dry_run_summary()
    assert summary["registers_on_startup"] is False
    assert summary["runs_background_loop"] is False
    assert summary["calls_apply_scan_job_update_plan"] is False
    assert summary["calls_scanner_adapter"] is False
    assert summary["mutates_attachment_scan_job"] is False


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
            "verify file",
        ):
            assert needle not in text, f"{page}: {needle}"


def test_no_db_migration_added() -> None:
    for name in ("f0012", "f0013", "f0014"):
        assert list(MIGRATIONS.glob(f"{name}*")) == []
    assert list(MIGRATIONS.glob("f0011*")) == [
        MIGRATIONS / "f0011_attachment_scan_queue.py"
    ]
    assert not list(MIGRATIONS.glob("*worker*"))


def test_related_summaries_remain_inactive() -> None:
    from app.platform.evidence.attachment_scan_admin_boundary import (
        scan_admin_boundary_summary,
    )
    from app.platform.evidence.attachment_quarantine_audit import (
        quarantine_audit_summary,
    )
    from app.platform.evidence.attachment_scan_result_persistence import (
        persistence_guard_summary,
    )

    assert scan_admin_boundary_summary().get("worker_controls_enabled") is False
    assert quarantine_audit_summary().get("worker_audit_emit_enabled") is False
    persist = persistence_guard_summary()
    assert persist.get("scan_admin_override_active") is False
    assert persist.get("scan_worker_active") is False
    assert DRY_RUN_MODULE.exists()
