"""Structural verification for Genesis III-A3."""

from __future__ import annotations

import ast
from pathlib import Path

REQUIRED_FILES = (
    Path("core/cognition/workspace/catalog.py"),
    Path("tests/test_genesis_3a3_workspace_catalog_search.py"),
    Path("docs/architecture/genesis_cognitive_workspace_catalog_search.md"),
    Path("docs/decisions/ADR-GENESIS-III-A3.md"),
)

REQUIRED_SYMBOLS = (
    "class WorkspaceQuery",
    "class WorkspaceCatalogEntry",
    "class CognitiveWorkspaceCatalog",
    "class WorkspaceSortField",
    "class SortDirection",
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

    source = Path(
        "core/cognition/workspace/catalog.py"
    ).read_text(encoding="utf-8")

    for symbol in REQUIRED_SYMBOLS:
        if symbol not in source:
            print(f"[FAIL] Missing catalog symbol: {symbol}")
            return 1

    print("[PASS] Genesis III-A3 required files exist")
    print("[PASS] Genesis III-A3 Python sources parse")
    print("[PASS] Catalog query and search contracts exist")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
