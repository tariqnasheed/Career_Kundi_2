"""Local scanner integration policy tests (0053-F19). Planning only."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from app.main import app
from app.platform.evidence.attachment_safety import (
    AttachmentSafetyStatus,
    attachment_safety_fields,
)
from app.platform.evidence.attachment_scanner_adapter import (
    NoopUnavailableScannerAdapter,
    get_configured_attachment_scanner_adapter,
)
from app.platform.evidence.attachment_scanner_policy import (
    CURRENT_SCANNER_ADAPTER_NAME,
    EXTERNAL_SCANNER_APIS_ALLOWED,
    FILE_PARSING_ALLOWED_FOR_MALWARE_SCAN,
    FUTURE_SCANNER_ADAPTER_FAMILY,
    LLM_FILE_REVIEW_ALLOWED,
    OCR_ALLOWED_FOR_MALWARE_SCAN,
    REAL_SCANNER_ENABLED,
    current_scanner_adapter_name,
    external_scanner_apis_allowed,
    file_parsing_allowed_for_malware_scan,
    future_local_scanner_requirements,
    future_mutation_targets_forbidden,
    future_scan_job_fields_may_update,
    future_scanner_adapter_family,
    llm_file_review_allowed,
    ocr_allowed_for_malware_scan,
    real_scanner_is_enabled,
    scanner_integration_policy_summary,
    select_configured_scanner_adapter_name,
)

REPO_ROOT = Path(__file__).resolve().parents[5]
EVIDENCE_PKG = REPO_ROOT / "backend" / "app" / "platform" / "evidence"
PYPROJECT = REPO_ROOT / "backend" / "pyproject.toml"
FRONTEND_PAGES = [
    REPO_ROOT / "frontend" / "src" / "pages" / "EvidenceLibraryPage.tsx",
    REPO_ROOT
    / "frontend"
    / "src"
    / "features"
    / "passport"
    / "PassportEvidencePanel.tsx",
]
SCHEMA = REPO_ROOT / "backend" / "app" / "schemas" / "evidence.py"


def test_real_scanner_disabled_and_noop_selected() -> None:
    assert REAL_SCANNER_ENABLED is False
    assert real_scanner_is_enabled() is False
    assert CURRENT_SCANNER_ADAPTER_NAME == "noop_unavailable"
    assert current_scanner_adapter_name() == "noop_unavailable"
    assert select_configured_scanner_adapter_name() == "noop_unavailable"
    adapter = get_configured_attachment_scanner_adapter()
    assert isinstance(adapter, NoopUnavailableScannerAdapter)


def test_external_parsing_llm_flags_false_and_family_local() -> None:
    assert EXTERNAL_SCANNER_APIS_ALLOWED is False
    assert external_scanner_apis_allowed() is False
    assert FILE_PARSING_ALLOWED_FOR_MALWARE_SCAN is False
    assert file_parsing_allowed_for_malware_scan() is False
    assert LLM_FILE_REVIEW_ALLOWED is False
    assert llm_file_review_allowed() is False
    assert OCR_ALLOWED_FOR_MALWARE_SCAN is False
    assert ocr_allowed_for_malware_scan() is False
    assert FUTURE_SCANNER_ADAPTER_FAMILY == "local_process_scanner"
    assert future_scanner_adapter_family() == "local_process_scanner"


def test_policy_summary_is_safe_and_not_verification() -> None:
    summary = scanner_integration_policy_summary()
    assert summary.real_scanner_enabled is False
    assert summary.applies_results_to_database is False
    assert summary.is_verification is False
    assert "planned only" in summary.warning.lower()
    blob = str(summary).lower()
    for phrase in (
        "safe file",
        "clean file",
        "trusted file",
        "verified document",
    ):
        assert phrase not in blob


def test_future_requirements_and_job_field_boundaries() -> None:
    reqs = future_local_scanner_requirements()
    assert any("bounded timeout" in r.lower() for r in reqs)
    assert any("path containment" in r.lower() for r in reqs)
    assert any("never mutate claimrecord" in r.lower() for r in reqs)
    allowed = future_scan_job_fields_may_update()
    assert "job_status" in allowed
    assert "attachment_safety_status" in allowed
    assert "safe_error_code" in allowed
    forbidden = future_mutation_targets_forbidden()
    assert "ClaimRecord.verification_status" in forbidden
    assert "ReviewRequest.review_state" in forbidden


def test_no_scanner_packages_in_pyproject() -> None:
    text = PYPROJECT.read_text(encoding="utf-8").lower()
    for needle in (
        "clamav",
        "pyclamd",
        "clamd",
        "virustotal",
        "pytesseract",
        "pdfplumber",
        "easyocr",
    ):
        assert needle not in text, needle


def test_no_real_adapter_classes_or_subprocess_scanner_calls() -> None:
    for path in EVIDENCE_PKG.rglob("*.py"):
        if "tests" in path.parts:
            continue
        source = path.read_text(encoding="utf-8")
        assert "ClamAVScannerAdapter" not in source
        assert "VirusTotalScannerAdapter" not in source
        assert "scan_file_with_clamav" not in source
        assert "scan_file_with_virustotal" not in source
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                mod = node.module.lower()
                assert "subprocess" not in mod
                assert "clamav" not in mod
                assert "virustotal" not in mod
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name.lower()
                    assert "subprocess" not in name
                    assert "clamav" not in name


def test_no_scan_routes_or_ui_and_public_safety_unchanged() -> None:
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

    fields = attachment_safety_fields()
    assert fields["attachment_safety_status"] == AttachmentSafetyStatus.SCAN_NOT_AVAILABLE.value
    schema = SCHEMA.read_text(encoding="utf-8")
    assert 'attachment_safety_status: str = "scan_not_available"' in schema
    # No raw scanner output / absolute path exposure fields on public schema.
    for forbidden in (
        "raw_scanner_output",
        "scanner_stdout",
        "filesystem_path",
        "absolute_path",
        "local_path",
    ):
        assert forbidden not in schema


def test_no_f0012_migration_and_policy_module_exists() -> None:
    migrations = (
        REPO_ROOT
        / "backend"
        / "app"
        / "db"
        / "foundation_migrations"
        / "versions"
    )
    assert list(migrations.glob("f0012*")) == []
    assert (EVIDENCE_PKG / "attachment_scanner_policy.py").exists()
    # Policy must not import config/env toggles for enabling scanners.
    policy_src = (EVIDENCE_PKG / "attachment_scanner_policy.py").read_text(
        encoding="utf-8"
    )
    assert "app.core.config" not in policy_src
    assert "os.environ" not in policy_src
    assert "getenv" not in policy_src
    assert re.search(
        r"REAL_SCANNER_ENABLED(?:\s*:\s*[^=]+)?\s*=\s*False", policy_src
    )
