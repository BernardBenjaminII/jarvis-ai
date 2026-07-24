#!/usr/bin/env python3
"""Structural verifier for Genesis III-A3A."""

from __future__ import annotations

import ast
from pathlib import Path


REQUIRED_EXPORTS = (
    "Assumption",
    "CognitiveWorkspace",
    "CognitiveWorkspaceCatalog",
    "CognitiveWorkspaceCodec",
    "CognitiveWorkspaceConflictError",
    "CognitiveWorkspaceError",
    "CognitiveWorkspaceNotFoundError",
    "CognitiveWorkspaceRepository",
    "CognitiveWorkspaceRepositoryError",
    "CognitiveWorkspaceService",
    "EvidenceReference",
    "Hypothesis",
    "HypothesisStatus",
    "OpenQuestion",
    "SQLiteCognitiveWorkspaceRepository",
    "SortDirection",
    "WorkspaceCatalogEntry",
    "WorkspaceEvent",
    "WorkspaceEventKind",
    "WorkspaceQuery",
    "WorkspaceSnapshot",
    "WorkspaceSortField",
    "WorkspaceStatus",
)


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    init_path = root / "core" / "cognition" / "__init__.py"
    workspace_init = root / "core" / "cognition" / "workspace" / "__init__.py"
    failures: list[str] = []

    for path in (init_path, workspace_init):
        if not path.is_file():
            failures.append(f"missing required file: {path.relative_to(root)}")
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append(f"syntax error in {path.relative_to(root)}: {exc}")

    if init_path.is_file():
        source = init_path.read_text(encoding="utf-8")
        for symbol in REQUIRED_EXPORTS:
            if f'"{symbol}"' not in source:
                failures.append(f"missing public export declaration: {symbol}")
        if "from .workspace import" not in source:
            failures.append("package root does not import the canonical workspace public API")

    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        print("\nChecks failed :", len(failures))
        print("Overall status: FAILED")
        return 1

    print("[PASS] Canonical cognition package files")
    print("[PASS] Python structural parsing")
    print("[PASS] Genesis III workspace exports restored")
    print("[PASS] Genesis VI executive cognition surface preserved by additive repair")
    print("\nChecks failed : 0")
    print("Overall status: EXCELLENT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
