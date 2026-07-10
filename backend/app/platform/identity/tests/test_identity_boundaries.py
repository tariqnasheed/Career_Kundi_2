"""Identity refs package must stay framework/feature free."""

from __future__ import annotations

import ast
from pathlib import Path

REFS = Path(__file__).resolve().parents[1] / "refs.py"
INIT = Path(__file__).resolve().parents[1] / "__init__.py"

_FORBIDDEN = (
    "app.agents",
    "app.api",
    "app.services",
    "app.features",
    "sqlalchemy",
    "fastapi",
    "pydantic",
    "frontend",
)


def test_refs_module_forbidden_imports() -> None:
    violations: list[str] = []
    for path in (REFS, INIT):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            mods: list[str] = []
            if isinstance(node, ast.Import):
                mods.extend(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods.append(node.module)
            for mod in mods:
                if mod.startswith("app.platform.kernel") or mod.startswith(
                    "app.platform.identity"
                ):
                    continue
                for prefix in _FORBIDDEN:
                    if mod == prefix or mod.startswith(prefix + "."):
                        violations.append(f"{path.name}: {mod}")
    assert not violations, violations
