"""Narrow import-boundary checks for the platform kernel."""

from __future__ import annotations

import ast
from pathlib import Path

KERNEL_DIR = Path(__file__).resolve().parents[1]

_FORBIDDEN_PREFIXES = (
    "app.agents",
    "app.api",
    "app.services",
    "app.features",
    "frontend",
)


def _kernel_python_files() -> list[Path]:
    return [
        p
        for p in KERNEL_DIR.rglob("*.py")
        if "tests" not in p.parts and p.name != "__pycache__"
    ]


def test_kernel_sources_have_no_forbidden_imports() -> None:
    violations: list[str] = []
    for path in _kernel_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)
            for mod in modules:
                if mod.startswith("app.platform.kernel"):
                    continue
                if mod == "app.platform" or mod.startswith("app.platform."):
                    # Kernel may only import within kernel; block other platform domains.
                    if not mod.startswith("app.platform.kernel"):
                        violations.append(f"{path.name}: {mod}")
                        continue
                for prefix in _FORBIDDEN_PREFIXES:
                    if mod == prefix or mod.startswith(prefix + "."):
                        violations.append(f"{path.name}: {mod}")
    assert not violations, "forbidden kernel imports:\n" + "\n".join(violations)


def test_kernel_has_no_sqlalchemy_or_pydantic() -> None:
    violations: list[str] = []
    for path in _kernel_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)
            for mod in modules:
                if mod == "sqlalchemy" or mod.startswith("sqlalchemy."):
                    violations.append(f"{path.name}: {mod}")
                if mod == "pydantic" or mod.startswith("pydantic."):
                    violations.append(f"{path.name}: {mod}")
    assert not violations, violations
