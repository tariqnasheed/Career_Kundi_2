"""Quarantine event/audit planning + disabled sink tests (0053-F24)."""

from __future__ import annotations

import ast
from pathlib import Path
from uuid import uuid4

import pytest

from app.main import app
from app.platform.evidence.attachment_quarantine_audit import (
    QUARANTINE_AUDIT_DB_ENABLED,
    QUARANTINE_AUDIT_FILE_LOG_ENABLED,
    QUARANTINE_AUDIT_PUBLIC_ACCESS_ENABLED,
    QUARANTINE_AUDIT_SINK_ENABLED,
    RAW_FILE_PATH_ALLOWED_IN_AUDIT,
    RAW_SCANNER_OUTPUT_ALLOWED_IN_AUDIT,
    STORAGE_URI_ALLOWED_IN_AUDIT,
    QuarantineAuditEventType,
    QuarantineAuditMode,
    build_quarantine_audit_event,
    current_quarantine_audit_plan,
    disabled_quarantine_audit_sink,
    quarantine_audit_is_enabled,
    quarantine_audit_summary,
    quarantine_audit_warning,
    sanitize_quarantine_audit_value,
)
from app.platform.evidence.attachment_scanner_runtime_policy import (
    REDACTED_PATH_MARKER,
)

REPO_ROOT = Path(__file__).resolve().parents[5]
AUDIT_MODULE = (
    REPO_ROOT
    / "backend"
    / "app"
    / "platform"
    / "evidence"
    / "attachment_quarantine_audit.py"
)
EVIDENCE_PKG = REPO_ROOT / "backend" / "app" / "platform" / "evidence"
QUARANTINE_DIR = REPO_ROOT / "backend" / "data" / "evidence_quarantine"
AUDIT_LOG_DIR = REPO_ROOT / "backend" / "data" / "evidence_audit"
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
PERSIST = EVIDENCE_PKG / "attachment_scan_result_persistence.py"


def test_audit_flags_are_disabled() -> None:
    assert QUARANTINE_AUDIT_SINK_ENABLED is False
    assert QUARANTINE_AUDIT_DB_ENABLED is False
    assert QUARANTINE_AUDIT_FILE_LOG_ENABLED is False
    assert QUARANTINE_AUDIT_PUBLIC_ACCESS_ENABLED is False
    assert RAW_FILE_PATH_ALLOWED_IN_AUDIT is False
    assert STORAGE_URI_ALLOWED_IN_AUDIT is False
    assert RAW_SCANNER_OUTPUT_ALLOWED_IN_AUDIT is False
    assert quarantine_audit_is_enabled() is False


def test_warning_and_plan_are_disabled() -> None:
    warning = quarantine_audit_warning().lower()
    assert "planned but not active" in warning
    assert "audit persistence" in warning
    plan = current_quarantine_audit_plan()
    assert plan.sink_enabled is False
    assert plan.db_enabled is False
    assert plan.file_log_enabled is False
    assert plan.public_access_enabled is False
    assert plan.mode is QuarantineAuditMode.DISABLED
    summary = quarantine_audit_summary()
    assert summary["persists_events"] is False
    assert summary["writes_files"] is False
    assert summary["writes_db"] is False
    assert summary["admin_surface_enabled"] is False
    assert summary["worker_audit_emit_enabled"] is False
    assert summary["planned_mode"] == (
        QuarantineAuditMode.PLANNED_PRIVATE_AUDIT_SINK.value
    )


def test_audit_event_builder_metadata_only() -> None:
    eid = uuid4()
    jid = uuid4()
    event = build_quarantine_audit_event(
        event_type=QuarantineAuditEventType.SCAN_JOB_CREATED,
        evidence_id=eid,
        scan_job_id=jid,
        owner_user_id=uuid4(),
        actor_user_id=uuid4(),
        job_status="queued",
        attachment_safety_status="scan_pending",
        safe_error_code="scanner_unavailable",
        safe_error_message="Malware scanning is not available in this version.",
    )
    assert event.event_type is QuarantineAuditEventType.SCAN_JOB_CREATED
    assert event.event_version == "1"
    assert event.evidence_id == str(eid)
    assert event.scan_job_id == str(jid)
    assert event.job_status == "queued"
    assert event.attachment_safety_status == "scan_pending"
    assert event.safe_error_code == "scanner_unavailable"
    assert event.created_at
    for forbidden in (
        "file_path",
        "storage_uri",
        "raw_output",
        "scanner_stdout",
        "public_url",
    ):
        assert not hasattr(event, forbidden)


def test_builder_rejects_forbidden_extra_keys() -> None:
    with pytest.raises(ValueError, match="Forbidden"):
        build_quarantine_audit_event(
            event_type=QuarantineAuditEventType.SCAN_JOB_RESERVED,
            file_path="/tmp/secret.bin",
        )
    with pytest.raises(ValueError, match="Unknown"):
        build_quarantine_audit_event(
            event_type=QuarantineAuditEventType.SCAN_JOB_RESERVED,
            weird_field="x",
        )


def test_sanitizer_redacts_paths_uris_and_urls() -> None:
    assert (
        sanitize_quarantine_audit_value("/tmp/evidence_files/x.bin")
        == REDACTED_PATH_MARKER
    )
    assert (
        sanitize_quarantine_audit_value("local-evidence://owner/abc")
        == REDACTED_PATH_MARKER
    )
    assert (
        sanitize_quarantine_audit_value("https://example.com/file.pdf")
        == REDACTED_PATH_MARKER
    )
    assert sanitize_quarantine_audit_value("this is a trusted file") is None


def test_sanitizer_handles_raw_scanner_output() -> None:
    dump = "FOUND virus\n" + ("x" * 500)
    sanitized = sanitize_quarantine_audit_value(dump)
    assert sanitized is not None
    assert len(sanitized) <= 240
    assert sanitize_quarantine_audit_value("scanner_stdout: Infected") is None
    assert "raw_output" not in (sanitized or "").lower()


def test_disabled_sink_does_not_persist_or_create_files() -> None:
    event = build_quarantine_audit_event(
        event_type=QuarantineAuditEventType.QUARANTINE_STORAGE_INACTIVE_CONFIRMED,
        job_status="reserved",
    )
    existed_q = QUARANTINE_DIR.exists()
    existed_a = AUDIT_LOG_DIR.exists()
    result = disabled_quarantine_audit_sink(event)
    assert result.persisted is False
    assert result.reason == "audit_sink_disabled"
    assert result.sink_enabled is False
    assert QUARANTINE_DIR.exists() is existed_q
    assert AUDIT_LOG_DIR.exists() is existed_a
    assert not QUARANTINE_DIR.exists()
    assert not AUDIT_LOG_DIR.exists()


def test_module_has_no_forbidden_imports_or_helpers() -> None:
    source = AUDIT_MODULE.read_text(encoding="utf-8")
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
        "mkdir(",
        "write_text",
        "write_bytes",
        "read_bytes",
        "session.commit",
        "AsyncSession",
        "EvidenceRecord",
        "ClaimRecord",
        "ReviewRequest",
    ):
        assert needle not in source, needle


def test_persistence_guard_does_not_auto_emit_audit() -> None:
    source = PERSIST.read_text(encoding="utf-8")
    assert "disabled_quarantine_audit_sink" not in source
    assert "build_quarantine_audit_event" not in source
    assert "attachment_quarantine_audit" not in source
    # Summary may mention audit inactive without importing the sink.
    from app.platform.evidence.attachment_scan_result_persistence import (
        persistence_guard_summary,
    )

    summary = persistence_guard_summary()
    assert summary["quarantine_audit_active"] is False


def test_no_audit_db_migration() -> None:
    for name in ("f0012", "f0013", "f0014"):
        assert list(MIGRATIONS.glob(f"{name}*")) == []
    assert list(MIGRATIONS.glob("f0011*")) == [
        MIGRATIONS / "f0011_attachment_scan_queue.py"
    ]
    assert not list(MIGRATIONS.glob("*audit*"))


def test_no_audit_scan_quarantine_routes_or_ui() -> None:
    paths = set(app.openapi().get("paths", {}))
    for path in paths:
        lower = path.lower()
        if path.startswith("/api/v1/evidence"):
            for needle in ("/scan", "/quarantine", "/audit", "/rescan", "/release"):
                assert needle not in lower, path
        assert not path.startswith("/api/v1/verification")
        assert "/admin/audit" not in lower
        assert "/admin/scan" not in lower
        assert "/admin/quarantine" not in lower
    assert not (ROUTES / "audit.py").exists()
    assert not (ROUTES / "quarantine.py").exists()
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
            "verify file",
        ):
            assert needle not in text, f"{page}: {needle}"


def test_no_quarantine_directory_created() -> None:
    assert not QUARANTINE_DIR.exists()
    _ = quarantine_audit_summary()
    assert not QUARANTINE_DIR.exists()


def test_event_types_cover_planning_set() -> None:
    values = {e.value for e in QuarantineAuditEventType}
    for required in (
        "scan_job_created",
        "scan_job_reserved",
        "scan_result_plan_built",
        "scan_result_persistence_rejected",
        "scan_result_persisted_to_job",
        "quarantine_required_decision_built",
        "quarantine_storage_unavailable",
        "quarantine_storage_inactive_confirmed",
    ):
        assert required in values
