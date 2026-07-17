"""Quarantine storage planning + disabled store contract tests (0053-F23)."""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.main import app
from app.platform.evidence.attachment_quarantine_storage import (
    QUARANTINE_FILE_DELETION_ENABLED,
    QUARANTINE_FILE_MOVEMENT_ENABLED,
    QUARANTINE_PUBLIC_ACCESS_ENABLED,
    QUARANTINE_STORAGE_ENABLED,
    QuarantineStorageDecision,
    QuarantineStorageMode,
    assert_quarantine_storage_inactive,
    build_quarantine_storage_decision,
    current_quarantine_storage_plan,
    quarantine_storage_is_enabled,
    quarantine_storage_summary,
    quarantine_storage_warning,
)
from app.platform.evidence.attachment_safety import AttachmentSafetyStatus
from app.platform.evidence.attachment_scan_queue import AttachmentScanJobStatus
from app.platform.evidence.attachment_scan_result_persistence import (
    ScanJobPersistenceError,
    assert_scan_job_update_allowed,
    build_persistable_scan_job_update_plan,
    plan_is_persistable,
)
from app.platform.evidence.attachment_scan_worker import (
    ScanWorkerAction,
    ScannerVerdict,
)

REPO_ROOT = Path(__file__).resolve().parents[5]
STORAGE_MODULE = (
    REPO_ROOT
    / "backend"
    / "app"
    / "platform"
    / "evidence"
    / "attachment_quarantine_storage.py"
)
EVIDENCE_PKG = REPO_ROOT / "backend" / "app" / "platform" / "evidence"
QUARANTINE_DIR = REPO_ROOT / "backend" / "data" / "evidence_quarantine"
FRONTEND_PAGES = [
    REPO_ROOT / "frontend" / "src" / "pages" / "EvidenceLibraryPage.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "passport"
    / "PassportEvidencePanel.tsx",
]
ROUTES = REPO_ROOT / "backend" / "app" / "api" / "routes"
MIGRATIONS = (
    REPO_ROOT / "backend" / "app" / "db" / "foundation_migrations" / "versions"
)


def _job(status: str = "reserved") -> SimpleNamespace:
    return SimpleNamespace(job_status=status)


def test_quarantine_storage_flags_are_disabled() -> None:
    assert QUARANTINE_STORAGE_ENABLED is False
    assert QUARANTINE_FILE_MOVEMENT_ENABLED is False
    assert QUARANTINE_FILE_DELETION_ENABLED is False
    assert QUARANTINE_PUBLIC_ACCESS_ENABLED is False
    assert quarantine_storage_is_enabled() is False


def test_current_storage_plan_is_disabled_planned_only() -> None:
    plan = current_quarantine_storage_plan()
    assert plan.storage_enabled is False
    assert plan.file_movement_enabled is False
    assert plan.file_deletion_enabled is False
    assert plan.public_access_enabled is False
    assert plan.mode is QuarantineStorageMode.DISABLED
    summary = quarantine_storage_summary()
    assert summary["mode"] == "disabled"
    assert summary["planned_mode"] == (
        QuarantineStorageMode.PLANNED_LOCAL_PRIVATE_STORE.value
    )
    assert summary["creates_directories"] is False
    assert summary["moves_files"] is False
    assert summary["deletes_files"] is False
    assert summary["copies_files"] is False
    assert summary["audit_sink_enabled"] is False
    assert summary["admin_controls_enabled"] is False


def test_warning_says_planned_but_not_active() -> None:
    warning = quarantine_storage_warning().lower()
    assert "planned but not active" in warning
    assert "quarantine storage" in warning
    for phrase in (
        "safe file",
        "clean file",
        "trusted file",
        "verified document",
        "official document",
    ):
        assert phrase not in warning


def test_quarantine_required_decision_is_object_only() -> None:
    for source in (
        ScannerVerdict.MALICIOUS,
        ScannerVerdict.SUSPICIOUS,
        AttachmentSafetyStatus.SCAN_FAILED,
        "malicious",
    ):
        decision = build_quarantine_storage_decision(source)
        assert decision is QuarantineStorageDecision.QUARANTINE_REQUIRED
    assert quarantine_storage_is_enabled() is False
    assert_quarantine_storage_inactive()


def test_not_required_and_unavailable_decisions() -> None:
    assert (
        build_quarantine_storage_decision(ScannerVerdict.CLEAN)
        is QuarantineStorageDecision.QUARANTINE_NOT_REQUIRED
    )
    assert (
        build_quarantine_storage_decision(AttachmentSafetyStatus.SCAN_PASSED)
        is QuarantineStorageDecision.QUARANTINE_NOT_REQUIRED
    )
    assert (
        build_quarantine_storage_decision(ScannerVerdict.ERROR)
        is QuarantineStorageDecision.QUARANTINE_UNAVAILABLE
    )
    assert (
        build_quarantine_storage_decision(ScannerVerdict.NOT_RUN)
        is QuarantineStorageDecision.QUARANTINE_UNAVAILABLE
    )


def test_assert_inactive_does_not_create_directories() -> None:
    existed_before = QUARANTINE_DIR.exists()
    assert_quarantine_storage_inactive()
    assert QUARANTINE_DIR.exists() is existed_before
    assert not QUARANTINE_DIR.exists()


def test_no_quarantine_directory_is_created() -> None:
    assert not QUARANTINE_DIR.exists()
    _ = current_quarantine_storage_plan()
    _ = quarantine_storage_summary()
    assert_quarantine_storage_inactive()
    assert not QUARANTINE_DIR.exists()


def test_no_file_move_copy_delete_helpers_exist() -> None:
    source = STORAGE_MODULE.read_text(encoding="utf-8")
    for forbidden in (
        "def move_to_quarantine",
        "def delete_quarantined_file",
        "def copy_to_quarantine",
        "def release_from_quarantine",
        "shutil",
        "os.remove",
        "os.rename",
        "unlink(",
        "rmtree(",
        "mkdir(",
        "Path(",
        "open(",
        "read_bytes",
        "write_bytes",
    ):
        assert forbidden not in source, forbidden


def test_storage_module_has_no_forbidden_imports() -> None:
    source = STORAGE_MODULE.read_text(encoding="utf-8")
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
        "clamav",
        "pyclamd",
        "virustotal",
        "pytesseract",
        "pdfminer",
        "pypdf",
        "PIL",
        "sqlalchemy",
        "app.tools.llm",
        "openai",
        "anthropic",
        "groq",
        "together",
    ):
        assert forbidden not in imports, forbidden
    assert "import subprocess" not in source
    assert "pathlib" not in source


def test_f22_persistence_still_rejects_quarantined() -> None:
    plan = build_persistable_scan_job_update_plan(
        action=ScanWorkerAction.COMPLETE_FAILED,
        job_status=AttachmentScanJobStatus.COMPLETED.value,
        attachment_safety_status=AttachmentSafetyStatus.QUARANTINED.value,
        quarantine_required=True,
    )
    assert plan.quarantine_required is True
    assert plan_is_persistable(plan) is True
    with pytest.raises(ScanJobPersistenceError, match="quarantined"):
        assert_scan_job_update_allowed(_job("reserved"), plan)


def test_quarantine_required_plan_does_not_imply_file_ops() -> None:
    plan = build_persistable_scan_job_update_plan(
        action=ScanWorkerAction.QUARANTINE_REQUIRED,
        job_status=AttachmentScanJobStatus.COMPLETED.value,
        attachment_safety_status=AttachmentSafetyStatus.SCAN_FAILED.value,
        quarantine_required=True,
    )
    assert plan.quarantine_required is True
    assert quarantine_storage_is_enabled() is False
    assert_quarantine_storage_inactive()
    assert_scan_job_update_allowed(_job("reserved"), plan)


def test_no_scan_or_quarantine_routes() -> None:
    paths = set(app.openapi().get("paths", {}))
    for path in paths:
        if path.startswith("/api/v1/evidence"):
            assert "/scan" not in path.lower(), path
            assert "/quarantine" not in path.lower(), path
            assert "/rescan" not in path.lower(), path
            assert "/release" not in path.lower(), path
            assert "/share" not in path.lower(), path
            assert "/public" not in path.lower(), path
        assert not path.startswith("/api/v1/verification")
        assert "/admin/scan" not in path.lower()
        assert "/admin/quarantine" not in path.lower()
    assert not (ROUTES / "quarantine.py").exists()
    assert not (ROUTES / "scan_jobs.py").exists()
    assert not (ROUTES / "admin_quarantine.py").exists()


def test_no_scan_or_quarantine_ui() -> None:
    for page in FRONTEND_PAGES:
        text = page.read_text(encoding="utf-8").lower()
        for needle in (
            "scan now",
            "rescan",
            "mark safe",
            "mark clean",
            "quarantine",
            "release from quarantine",
            "verify file",
        ):
            assert needle not in text, f"{page}: {needle}"


def test_no_db_migration_added() -> None:
    for name in ("f0012", "f0013", "f0014"):
        matches = list(MIGRATIONS.glob(f"{name}*"))
        assert matches == [], matches
    assert list(MIGRATIONS.glob("f0011*")) == [
        MIGRATIONS / "f0011_attachment_scan_queue.py"
    ]


def test_storage_module_has_no_db_mutation_surface() -> None:
    source = STORAGE_MODULE.read_text(encoding="utf-8")
    for forbidden in (
        "AsyncSession",
        "session.commit",
        "EvidenceRecord",
        "ClaimRecord",
        "ReviewRequest",
        "AttachmentScanJob",
    ):
        assert forbidden not in source, forbidden


def test_disabled_contract_module_exists_and_generic_quarantine_absent() -> None:
    assert STORAGE_MODULE.exists()
    assert not (EVIDENCE_PKG / "quarantine.py").exists()
    assert (EVIDENCE_PKG / "attachment_quarantine_policy.py").exists()
