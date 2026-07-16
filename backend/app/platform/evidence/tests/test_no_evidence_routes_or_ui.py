"""Boundary guards for evidence domain (0053-F2/F3)."""

from __future__ import annotations

import ast
from pathlib import Path

from app.main import app

REPO_ROOT = Path(__file__).resolve().parents[5]
BACKEND = REPO_ROOT / "backend"
EVIDENCE_PKG = BACKEND / "app" / "platform" / "evidence"
ROUTES = BACKEND / "app" / "api" / "routes"
FRONTEND_SRC = REPO_ROOT / "frontend" / "src"

FORBIDDEN_IMPORT_PREFIXES = (
    "app.career_passport",
    "app.api.routes.passport",
    "app.api.routes.cv_builder",
    "app.api.routes.roadmap",
    "app.api.routes.job_search",
    "frontend",
)


def _py_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if p.is_file())


def test_private_evidence_route_exists_without_claims_or_upload() -> None:
    """F3 adds private evidence routes; still no claims/upload/download/share."""
    assert (ROUTES / "evidence.py").exists()
    assert not (ROUTES / "claims.py").exists()
    paths = set(app.openapi().get("paths", {}))
    assert any(p.startswith("/api/v1/evidence") for p in paths)
    for path in paths:
        lower = path.lower()
        if "/api/v1/evidence" not in lower:
            continue
        assert "/upload" not in lower
        assert "/download" not in lower
        assert "/share" not in lower
        assert "/public" not in lower


def test_evidence_module_avoids_feature_domain_imports() -> None:
    for path in _py_files(EVIDENCE_PKG):
        if "tests" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for prefix in FORBIDDEN_IMPORT_PREFIXES:
                    assert not mod.startswith(prefix), f"{path}: imports {mod}"
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for prefix in FORBIDDEN_IMPORT_PREFIXES:
                        assert not alias.name.startswith(prefix), (
                            f"{path}: imports {alias.name}"
                        )


def test_claims_module_does_not_own_evidence_implementation() -> None:
    """Claims must not import evidence service/models (no circular ownership)."""
    claims_pkg = BACKEND / "app" / "platform" / "claims"
    for path in _py_files(claims_pkg):
        if "tests" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                assert not mod.startswith("app.platform.evidence"), path
                assert not mod.startswith("app.db.models.evidence"), path
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("app.platform.evidence"), path
                    assert not alias.name.startswith("app.db.models.evidence"), path


def test_no_frontend_evidence_ui_paths() -> None:
    """F3 must not add frontend evidence/claim UI files."""
    if not FRONTEND_SRC.exists():
        return
    unexpected = []
    for path in FRONTEND_SRC.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        lower = rel.lower()
        if "evidence" in lower and "passport" not in lower:
            if "/features/" in lower or "/pages/" in lower:
                unexpected.append(rel)
    assert unexpected == [], unexpected
