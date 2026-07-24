#!/usr/bin/env python3
"""Structural verification for JARVIS Phase X."""

from __future__ import annotations

import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = (
    Path("core/reasoning/__init__.py"),
    Path("core/reasoning/enums.py"),
    Path("core/reasoning/errors.py"),
    Path("core/reasoning/models.py"),
    Path("core/reasoning/confidence.py"),
    Path("core/reasoning/inference.py"),
    Path("core/reasoning/service.py"),
    Path("tests/test_phase_x_reasoning_foundation.py"),
    Path("docs/architecture/reasoning_engine_foundation.md"),
)

FORBIDDEN_IMPORT_PREFIXES = (
    "core.executive.engine",
    "core.executive.store",
    "core.executive.planner",
    "core.executive.director",
    "core.executive.mission_compiler",
)


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)

    return modules


def main() -> int:
    failures: list[str] = []

    for relative_path in REQUIRED_FILES:
        path = PROJECT_ROOT / relative_path
        if not path.is_file():
            failures.append(f"Missing required file: {relative_path}")
            continue

        if path.suffix == ".py":
            try:
                ast.parse(
                    path.read_text(encoding="utf-8"),
                    filename=str(relative_path),
                )
            except SyntaxError as exc:
                failures.append(
                    f"Syntax error in {relative_path}: {exc}"
                )

    reasoning_root = PROJECT_ROOT / "core" / "reasoning"
    if reasoning_root.is_dir():
        for path in reasoning_root.glob("*.py"):
            for module in imported_modules(path):
                if module.startswith(FORBIDDEN_IMPORT_PREFIXES):
                    failures.append(
                        f"{path.relative_to(PROJECT_ROOT)} imports "
                        f"forbidden execution dependency {module}"
                    )

    service = reasoning_root / "service.py"
    if service.is_file():
        text = service.read_text(encoding="utf-8")
        for forbidden in (".execute(", "subprocess", "requests.", "openai"):
            if forbidden in text:
                failures.append(
                    f"Reasoning service contains forbidden behavior: "
                    f"{forbidden}"
                )

    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1

    print("[PASS] Phase X Reasoning Engine structure is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
