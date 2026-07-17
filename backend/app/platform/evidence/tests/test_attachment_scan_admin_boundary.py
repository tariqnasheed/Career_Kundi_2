"""Scan/quarantine admin boundary planning tests (0053-F25)."""

from __future__ import annotations

import ast
from pathlib import Path

from app.main import app
from app.platform.evidence.attachment_scan_admin_boundary import (
    SCAN_ADMIN_API_ENABLED,
    SCAN_ADMIN_CAN_DELETE_ATTACHMENT,
    SCAN_ADMIN_CAN_FORCE_SCAN,
    SCAN_ADMIN_CAN_MARK_CLEAN,
    SCAN_ADMIN_CAN_MARK_SAFE,
    SCAN_ADMIN_CAN_RELEASE_QUARANTINE,
    SCAN_ADMIN_CAN_VERIFY_CLAIM,
    SCAN_ADMIN_CAN_VERIFY_DOCUMENT,
    SCAN_ADMIN_CAN_VIEW_RAW_FILE_PATH,
    SCAN_ADMIN_CAN_VIEW_RAW_SCANNER_OUTPUT,
    SCAN_ADMIN_CAN_VIEW_STORAGE_URI,
    SCAN_ADMIN_SURFACE_ENABLED,
    SCAN_ADMIN_UI_ENABLED,
    ScanAdminForbiddenAction,
    ScanAdminFutureAction,
    ScanAdminSurfaceMode,
    assert_scan_admin_surface_disabled,
    current_scan_admin_boundary_plan,
    forbidden_scan_admin_actions,
    planned_scan_admin_actions,
    scan_admin_boundary_summary,
    scan_admin_boundary_warning,
    scan_admin_surface_is_enabled,
)

REPO_ROOT = Path(__file__).resolve().parents[5]
ADMIN_MODULE = (
    REPO_ROOT
    / "backend"
    / "app"
    / "platform"
    / "evidence"
    / "attachment_scan_admin_boundary.py"
)
EVIDENCE_PKG = REPO_ROOT / "backend" / "app" / "platform" / "evidence"
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
QUARANTINE_DIR = REPO_ROOT / "backend" / "data" / "evidence_quarantine"
AUDIT_DIR = REPO_ROOT / "backend" / "data" / "evidence_audit"


def test_admin_flags_are_disabled() -> None:
    assert SCAN_ADMIN_SURFACE_ENABLED is False
    assert SCAN_ADMIN_API_ENABLED is False
    assert SCAN_ADMIN_UI_ENABLED is False
    assert SCAN_ADMIN_CAN_FORCE_SCAN is False
    assert SCAN_ADMIN_CAN_MARK_SAFE is False
    assert SCAN_ADMIN_CAN_MARK_CLEAN is False
    assert SCAN_ADMIN_CAN_VERIFY_DOCUMENT is False
    assert SCAN_ADMIN_CAN_VERIFY_CLAIM is False
    assert SCAN_ADMIN_CAN_RELEASE_QUARANTINE is False
    assert SCAN_ADMIN_CAN_DELETE_ATTACHMENT is False
    assert SCAN_ADMIN_CAN_VIEW_RAW_FILE_PATH is False
    assert SCAN_ADMIN_CAN_VIEW_STORAGE_URI is False
    assert SCAN_ADMIN_CAN_VIEW_RAW_SCANNER_OUTPUT is False
    assert scan_admin_surface_is_enabled() is False


def test_plan_mode_and_warning() -> None:
    plan = current_scan_admin_boundary_plan()
    assert plan.surface_enabled is False
    assert plan.api_enabled is False
    assert plan.ui_enabled is False
    assert plan.mode is ScanAdminSurfaceMode.DISABLED
    warning = scan_admin_boundary_warning().lower()
    assert "planned but not active" in warning
    assert "admin controls" in warning


def test_planned_actions_exclude_trust_powers() -> None:
    planned = set(planned_scan_admin_actions())
    assert planned == {a.value for a in ScanAdminFutureAction}
    for forbidden in (
        "mark_file_safe",
        "mark_file_clean",
        "verify_document",
        "verify_claim",
        "publish_file",
        "release_quarantine",
    ):
        assert forbidden not in planned


def test_forbidden_actions_cover_trust_and_leak_powers() -> None:
    forbidden = set(forbidden_scan_admin_actions())
    assert forbidden == {a.value for a in ScanAdminForbiddenAction}
    for required in (
        "mark_file_safe",
        "mark_file_clean",
        "verify_document",
        "verify_claim",
        "expose_storage_uri",
        "expose_raw_scanner_output",
        "override_claim_status",
        "override_review_state",
        "release_quarantine",
        "delete_attachment_as_quarantine",
        "publish_file",
    ):
        assert required in forbidden


def test_summary_says_no_mutation_powers() -> None:
    summary = scan_admin_boundary_summary()
    assert summary["has_mutation_powers"] is False
    assert summary["mutates_evidence_record"] is False
    assert summary["mutates_claim_record"] is False
    assert summary["mutates_review_request"] is False
    assert summary["is_verification"] is False
    assert summary["is_admin_feature"] is False
    assert summary["can_mark_safe"] is False
    assert summary["can_verify_claim"] is False
    assert summary["can_view_raw_file_path"] is False
    assert summary["can_view_storage_uri"] is False
    assert summary["can_view_raw_scanner_output"] is False


def test_assert_disabled_does_not_create_artifacts() -> None:
    existed_q = QUARANTINE_DIR.exists()
    existed_a = AUDIT_DIR.exists()
    assert_scan_admin_surface_disabled()
    assert QUARANTINE_DIR.exists() is existed_q
    assert AUDIT_DIR.exists() is existed_a
    assert not QUARANTINE_DIR.exists()
    assert not AUDIT_DIR.exists()
    assert not (ROUTES / "admin_scan.py").exists()
    assert not (ROUTES / "admin_quarantine.py").exists()
    assert not (ROUTES / "audit.py").exists()


def test_module_has_no_forbidden_imports() -> None:
    source = ADMIN_MODULE.read_text(encoding="utf-8")
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
        "virustotal",
        "pytesseract",
        "pdfminer",
        "pypdf",
        "sqlalchemy",
        "fastapi",
        "openai",
        "anthropic",
        "groq",
        "together",
        "app.tools.llm",
    ):
        assert forbidden not in imports, forbidden
    for needle in (
        "import subprocess",
        "open(",
        "Path(",
        "AsyncSession",
        "session.commit",
        "EvidenceRecord",
        "ClaimRecord",
        "ReviewRequest",
        "APIRouter",
        "read_bytes",
        "write_bytes",
    ):
        assert needle not in source, needle


def test_no_admin_scan_quarantine_audit_routes() -> None:
    paths = set(app.openapi().get("paths", {}))
    for path in paths:
        lower = path.lower()
        if path.startswith("/api/v1/evidence"):
            for needle in (
                "/scan",
                "/quarantine",
                "/audit",
                "/admin",
                "/rescan",
                "/release",
            ):
                assert needle not in lower, path
        assert not path.startswith("/api/v1/verification")
        assert not path.startswith("/api/v1/admin")
        assert "/admin/scan" not in lower
        assert "/admin/quarantine" not in lower
        assert "/admin/audit" not in lower
    assert not (ROUTES / "admin_scan.py").exists()
    assert not (ROUTES / "admin_quarantine.py").exists()
    assert not (ROUTES / "audit.py").exists()
    assert not (ROUTES / "quarantine.py").exists()


def test_no_frontend_admin_scan_quarantine_audit_ui() -> None:
    for page in FRONTEND_PAGES:
        text = page.read_text(encoding="utf-8").lower()
        for needle in (
            "scan now",
            "rescan",
            "mark safe",
            "mark clean",
            "quarantine",
            "audit log",
            "view audit",
            "admin panel",
            "security operator",
            "verify file",
            "verify document",
        ):
            assert needle not in text, f"{page}: {needle}"


def test_no_db_migration_added() -> None:
    for name in ("f0012", "f0013", "f0014"):
        assert list(MIGRATIONS.glob(f"{name}*")) == []
    assert list(MIGRATIONS.glob("f0011*")) == [
        MIGRATIONS / "f0011_attachment_scan_queue.py"
    ]
    assert not list(MIGRATIONS.glob("*admin*"))
    assert not list(MIGRATIONS.glob("*audit*"))


def test_persistence_and_related_summaries_remain_inactive() -> None:
    from app.platform.evidence.attachment_scan_result_persistence import (
        persistence_guard_summary,
    )
    from app.platform.evidence.attachment_quarantine_audit import (
        quarantine_audit_summary,
    )
    from app.platform.evidence.attachment_quarantine_storage import (
        quarantine_storage_summary,
    )

    persist = persistence_guard_summary()
    assert persist.get("quarantine_audit_active") is False
    assert persist.get("scan_admin_override_active") is False
    assert quarantine_audit_summary().get("admin_surface_enabled") is False
    assert quarantine_storage_summary().get("admin_controls_enabled") is False
    assert ADMIN_MODULE.exists()
    assert not (EVIDENCE_PKG / "quarantine.py").exists()
