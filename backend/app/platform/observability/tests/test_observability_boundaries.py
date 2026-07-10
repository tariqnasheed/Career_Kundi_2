"""Observability package boundary + no-migration proofs (0050-PF10-S1)."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PURE_MODULES = (
    ROOT / "correlation.py",
    ROOT / "redaction.py",
    ROOT / "events.py",
    ROOT / "logging.py",
)
FOUNDATION_VERSIONS = (
    Path(__file__).resolve().parents[3]
    / "db"
    / "foundation_migrations"
    / "versions"
)
MODELS_DIR = Path(__file__).resolve().parents[3] / "db" / "models"

_FORBIDDEN = (
    "app.agents",
    "app.services",
    "job_search",
    "auto_apply",
    "frontend",
    "app.platform.claims",
    "app.platform.privacy",
    "app.db.models",
    "sqlalchemy",
    "datadog",
    "sentry",
    "newrelic",
    "honeycomb",
    "opentelemetry",
)


def test_pure_modules_forbidden_imports() -> None:
    violations: list[str] = []
    for path in PURE_MODULES:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            mods: list[str] = []
            if isinstance(node, ast.Import):
                mods.extend(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods.append(node.module)
            for mod in mods:
                if mod.startswith("app.platform.observability"):
                    continue
                for prefix in _FORBIDDEN:
                    if (
                        mod == prefix
                        or mod.startswith(prefix + ".")
                        or prefix in mod.split(".")
                    ):
                        violations.append(f"{path.name}: {mod}")
    assert not violations, violations


def test_no_vendor_sdk_imports_in_package() -> None:
    vendors = ("datadog", "sentry", "newrelic", "honeycomb", "opentelemetry")
    violations: list[str] = []
    for path in ROOT.rglob("*.py"):
        if "__pycache__" in path.parts or path.name == "test_observability_boundaries.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            mods: list[str] = []
            if isinstance(node, ast.Import):
                mods.extend(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods.append(node.module)
            for mod in mods:
                root = mod.split(".", 1)[0].lower()
                if root in vendors or any(v in mod.lower() for v in vendors):
                    violations.append(f"{path.name}: {mod}")
    assert not violations, violations


def test_no_f0008_or_observability_migration() -> None:
    names = {p.name for p in FOUNDATION_VERSIONS.glob("*.py") if p.name != "__init__.py"}
    assert not any(n.startswith("f0008") for n in names)
    assert not any("observability" in n.lower() for n in names)
    assert "f0007_privacy_foundation.py" in names


def test_no_observability_orm_models() -> None:
    model_names = {p.stem for p in MODELS_DIR.glob("*.py")}
    assert "observability" not in model_names
    forbidden_tables = {
        "observability_events",
        "request_logs",
        "telemetry_events",
        "trace_spans",
        "metric_points",
    }
    for path in MODELS_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for table in forbidden_tables:
            assert f'__tablename__ = "{table}"' not in text
            assert f"__tablename__ = '{table}'" not in text
