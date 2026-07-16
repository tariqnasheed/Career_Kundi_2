"""0053-F9 boundary: no verification routes, UI, DB model, migration, or LLM/OCR."""

from __future__ import annotations

import ast
from pathlib import Path

from app.main import app
from app.platform.verification.contracts import (
    map_review_outcome_to_claim_verification_status,
)

REPO_ROOT = Path(__file__).resolve().parents[5]
BACKEND = REPO_ROOT / "backend"
VERIFICATION_PKG = BACKEND / "app" / "platform" / "verification"
ROUTES = BACKEND / "app" / "api" / "routes"
MODELS = BACKEND / "app" / "db" / "models"
MIGRATION_ROOTS = (
    BACKEND / "app" / "db" / "migrations",
    BACKEND / "app" / "db" / "foundation_migrations",
)
FRONTEND_SRC = REPO_ROOT / "frontend" / "src"

FORBIDDEN_IMPORT_PREFIXES = (
    "app.tools.llm",
    "app.api.routes.passport",
    "app.api.routes.cv_builder",
    "app.api.routes.roadmap",
    "app.api.routes.job_search",
    "app.career_passport",
)

OCR_PARSE_HINTS = (
    "pytesseract",
    "pdfplumber",
    "pdfminer",
    "easyocr",
    "ocr_",
)


def _py_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if p.is_file())


def test_no_verification_api_route_module() -> None:
    assert not (ROUTES / "verification.py").exists()
    assert not (ROUTES / "claims.py").exists()
    paths = set(app.openapi().get("paths", {}))
    assert "/api/v1/verification" not in paths
    assert "/api/v1/claims/verify" not in paths
    for path in paths:
        lower = path.lower()
        if "/verify" in lower or lower.endswith("/verification"):
            if path.startswith("/api/v1/"):
                raise AssertionError(f"unexpected verification route: {path}")


def test_no_verification_review_model_or_migration() -> None:
    assert not (MODELS / "verification.py").exists()
    assert not (MODELS / "verification_review.py").exists()
    for migrations in MIGRATION_ROOTS:
        if not migrations.exists():
            continue
        for path in migrations.rglob("*"):
            if not path.is_file():
                continue
            name = path.name.lower()
            assert "verification_review" not in name
            assert "f0010_verification" not in name


def test_verification_package_avoids_llm_ocr_feature_imports() -> None:
    for path in _py_files(VERIFICATION_PKG):
        if "tests" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for prefix in FORBIDDEN_IMPORT_PREFIXES:
                    assert not mod.startswith(prefix), f"{path}: imports {mod}"
                assert not mod.startswith("app.db.models"), path
                assert "sqlalchemy" not in mod, path
                assert "fastapi" not in mod, path
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for prefix in FORBIDDEN_IMPORT_PREFIXES:
                        assert not alias.name.startswith(prefix), path
        lowered = text.lower()
        for hint in OCR_PARSE_HINTS:
            assert hint not in lowered, f"{path}: OCR/parsing hint {hint}"


def test_mapping_helper_not_imported_by_api_routes() -> None:
    """Current APIs must not call review outcome mapping."""
    for path in _py_files(ROUTES):
        text = path.read_text(encoding="utf-8")
        assert "map_review_outcome_to_claim_verification_status" not in text
        assert "validate_review_transition" not in text
        assert "app.platform.verification" not in text
    # Mapping exists for future services only.
    assert map_review_outcome_to_claim_verification_status("approved") is not None


def test_no_frontend_verify_controls() -> None:
    if not FRONTEND_SRC.exists():
        return
    targets = [
        FRONTEND_SRC / "features" / "passport" / "PassportPage.tsx",
        FRONTEND_SRC / "features" / "passport" / "PassportEvidencePanel.tsx",
        FRONTEND_SRC / "pages" / "EvidenceLibraryPage.tsx",
        FRONTEND_SRC / "pages" / "CVBuilderPage.tsx",
        FRONTEND_SRC / "pages" / "RoadmapPage.tsx",
        FRONTEND_SRC / "pages" / "JobSearchPage.tsx",
    ]
    forbidden_phrases = (
        "verify claim",
        "verified passport",
        "submit proof",
        "make official",
        "ai verified",
        "self verified",
    )
    # Safe F8 negation copy may say “does not verify … Passport”; strip before checks.
    safe_negations = (
        "does not verify your passport",
        "does not verify passport",
        "does not verify the claim",
        "does not verify a claim",
        "linking evidence does not verify",
        "not independently verified",
    )
    for path in targets:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8").lower()
        scrubbed = text
        for safe in safe_negations:
            scrubbed = scrubbed.replace(safe, "")
        for phrase in forbidden_phrases:
            assert phrase not in scrubbed, f"{path}: contains {phrase!r}"
        assert "verify passport" not in scrubbed, f"{path}: verify action copy"
        # No verify action button copy.
        assert ">verify<" not in scrubbed.replace(" ", "")
        assert "verify button" not in scrubbed
