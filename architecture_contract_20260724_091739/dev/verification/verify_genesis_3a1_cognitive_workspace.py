"""Structural verification for Genesis III-A1."""

from __future__ import annotations

import ast
from pathlib import Path


REQUIRED_FILES = (
    Path("core/cognition/__init__.py"),
    Path("core/cognition/workspace/__init__.py"),
    Path("core/cognition/workspace/enums.py"),
    Path("core/cognition/workspace/errors.py"),
    Path("core/cognition/workspace/models.py"),
    Path("core/cognition/workspace/service.py"),
    Path("tests/test_genesis_3a1_cognitive_workspace.py"),
    Path("docs/architecture/genesis_cognitive_workspace_foundation.md"),
    Path("docs/decisions/ADR-GENESIS-III-A1.md"),
)


def main() -> int:
    missing = [path.as_posix() for path in REQUIRED_FILES if not path.is_file()]
    if missing:
        for path in missing:
            print(f"[FAIL] Missing required file: {path}")
        return 1

    for path in REQUIRED_FILES:
        if path.suffix == ".py":
            ast.parse(path.read_text(encoding="utf-8"))

    print("[PASS] Genesis III-A1 required files exist")
    print("[PASS] Genesis III-A1 Python sources parse")
    print("[PASS] Cognitive workspace structural verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
