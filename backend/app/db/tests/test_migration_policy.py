"""Foundation migration policy / AST guards (0050-PF1-S1R1A)."""

from __future__ import annotations

import ast
from pathlib import Path

from alembic.script import ScriptDirectory

from app.db.migration_runner import (
    build_foundation_alembic_config,
    foundation_bases,
    foundation_heads,
)

VERSIONS = (
    Path(__file__).resolve().parents[1] / "foundation_migrations" / "versions"
)
RUNNER = Path(__file__).resolve().parents[1] / "migration_runner.py"
LEGACY_0001 = (
    Path(__file__).resolve().parents[1] / "migrations" / "versions" / "0001_initial.py"
)
FOUNDATION_BASELINE = "f0001_foundation_baseline"
FOUNDATION_CURRENT_HEAD = "f0008_passport_persistence"
FOUNDATION_F0002 = "f0002_identity_subject_stub"
FOUNDATION_F0003 = "f0003_provenance_source_snapshot"
FOUNDATION_F0004 = "f0004_claim_foundation"
FOUNDATION_F0005 = "f0005_geo_jurisdiction_locale"
FOUNDATION_F0006 = "f0006_lifecycle_loop_foundation"
FOUNDATION_F0007 = "f0007_privacy_foundation"


def _foundation_revision_files() -> list[Path]:
    return sorted(
        p for p in VERSIONS.glob("*.py") if p.name != "__init__.py" and p.stat().st_size > 0
    )


def test_single_base_and_head() -> None:
    assert foundation_bases() == [FOUNDATION_BASELINE]
    assert foundation_heads() == [FOUNDATION_CURRENT_HEAD]


def test_script_directory_single_lineage() -> None:
    script = ScriptDirectory.from_config(build_foundation_alembic_config())
    assert len(script.get_heads()) == 1
    assert len(script.get_bases()) == 1
    head = script.get_revision(FOUNDATION_CURRENT_HEAD)
    assert head is not None
    assert head.down_revision == FOUNDATION_F0007
    f0007 = script.get_revision(FOUNDATION_F0007)
    assert f0007 is not None
    assert f0007.down_revision == FOUNDATION_F0006
    f0006 = script.get_revision(FOUNDATION_F0006)
    assert f0006 is not None
    assert f0006.down_revision == FOUNDATION_F0005
    f0005 = script.get_revision(FOUNDATION_F0005)
    assert f0005 is not None
    assert f0005.down_revision == FOUNDATION_F0004
    f0004 = script.get_revision(FOUNDATION_F0004)
    assert f0004 is not None
    assert f0004.down_revision == FOUNDATION_F0003
    f0003 = script.get_revision(FOUNDATION_F0003)
    assert f0003 is not None
    assert f0003.down_revision == FOUNDATION_F0002
    mid = script.get_revision(FOUNDATION_F0002)
    assert mid is not None
    assert mid.down_revision == FOUNDATION_BASELINE
    base = script.get_revision(FOUNDATION_BASELINE)
    assert base is not None
    assert base.down_revision is None


def test_runner_has_no_create_all() -> None:
    tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr != "create_all"
            assert node.func.attr != "drop_all"


def test_foundation_revisions_forbid_create_all_drop_all_and_orm_imports() -> None:
    files = _foundation_revision_files()
    assert files, "expected foundation revision files"
    violations: list[str] = []
    for path in files:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in {"create_all", "drop_all"}:
                    violations.append(f"{path.name}:{node.lineno}:{node.func.attr}")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "app.db.models" or alias.name.startswith("app.db.models."):
                        violations.append(f"{path.name}:import {alias.name}")
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod == "app.db.models" or mod.startswith("app.db.models."):
                    violations.append(f"{path.name}:from {mod}")
                if mod == "app.db.base":
                    names = {a.name for a in node.names}
                    if "Base" in names or "*" in names:
                        violations.append(f"{path.name}:from app.db.base import Base")
    assert not violations, "\n".join(violations)


def test_baseline_upgrade_has_explicit_operations() -> None:
    path = VERSIONS / "f0001_foundation_baseline.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    upgrade_fn = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "upgrade":
            upgrade_fn = node
            break
    assert upgrade_fn is not None
    # Bare `pass` / empty upgrade is forbidden. op.create_table(...) is an Expr(Call).
    only_pass = all(isinstance(s, (ast.Pass, ast.Expr)) and not (
        isinstance(s, ast.Expr) and isinstance(s.value, ast.Call)
    ) for s in upgrade_fn.body)
    # Simpler: count create_table calls inside upgrade().
    create_calls = 0
    for node in ast.walk(upgrade_fn):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "create_table"
        ):
            create_calls += 1
    assert create_calls >= 10, f"expected many create_table ops, got {create_calls}"
    assert not only_pass or create_calls > 0



def test_rejected_0002_not_in_foundation_or_legacy_versions() -> None:
    rejected = "0002_pf1_migration_rails.py"
    assert not (VERSIONS / rejected).exists()
    legacy_versions = Path(__file__).resolve().parents[1] / "migrations" / "versions"
    assert not (legacy_versions / rejected).exists()


def test_legacy_0001_unchanged_on_disk_tracked() -> None:
    assert LEGACY_0001.exists()
    text = LEGACY_0001.read_text(encoding="utf-8")
    assert "revision = \"0001_initial\"" in text or "revision = '0001_initial'" in text
