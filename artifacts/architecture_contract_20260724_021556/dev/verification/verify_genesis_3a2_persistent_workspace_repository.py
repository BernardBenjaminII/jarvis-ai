"""Structural verification for Genesis III-A2."""

from __future__ import annotations

import ast
from pathlib import Path

REQUIRED_FILES = (
    Path("core/cognition/workspace/repository.py"),
    Path("tests/test_genesis_3a2_persistent_workspace_repository.py"),
    Path("docs/architecture/genesis_persistent_cognitive_workspace_repository.md"),
    Path("docs/decisions/ADR-GENESIS-III-A2.md"),
)


def main() -> int:
    missing = [str(path) for path in REQUIRED_FILES if not path.is_file()]
    if missing:
        for path in missing:
            print(f"[FAIL] Missing required file: {path}")
        return 1

    for path in REQUIRED_FILES:
        if path.suffix == ".py":
            ast.parse(path.read_text(encoding="utf-8"))

    repository_source = Path(
        "core/cognition/workspace/repository.py"
    ).read_text(encoding="utf-8")

    required_symbols = (
        "class CognitiveWorkspaceRepository",
        "class CognitiveWorkspaceCodec",
        "class SQLiteCognitiveWorkspaceRepository",
        "class CognitiveWorkspaceConflictError",
        "class CognitiveWorkspaceNotFoundError",
    )
    for symbol in required_symbols:
        if symbol not in repository_source:
            print(f"[FAIL] Missing repository symbol: {symbol}")
            return 1

    print("[PASS] Genesis III-A2 required files exist")
    print("[PASS] Genesis III-A2 Python sources parse")
    print("[PASS] Repository contracts and SQLite implementation exist")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
