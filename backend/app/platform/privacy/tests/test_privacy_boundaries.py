"""Privacy refs/kinds must stay framework/feature free."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PURE_MODULES = (ROOT / "refs.py", ROOT / "kinds.py", ROOT / "__init__.py")
README = ROOT / "README.md"

_FORBIDDEN = (
    "app.agents",
    "app.api",
    "app.services",
    "app.features",
    "app.platform.claims",
    "app.platform.provenance",
    "app.platform.geo",
    "app.platform.lifecycle",
    "sqlalchemy",
    "fastapi",
    "pydantic",
    "frontend",
    "legal_compliance",
)


def test_privacy_pure_modules_forbidden_imports() -> None:
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
                if mod.startswith("app.platform.kernel") or mod.startswith(
                    "app.platform.privacy"
                ):
                    continue
                for prefix in _FORBIDDEN:
                    if mod == prefix or mod.startswith(prefix + "."):
                        violations.append(f"{path.name}: {mod}")
    assert not violations, violations


def test_readme_disclaims_legal_compliance() -> None:
    text = README.read_text(encoding="utf-8")
    assert "do not by themselves make CareerKundi legally compliant" in text
