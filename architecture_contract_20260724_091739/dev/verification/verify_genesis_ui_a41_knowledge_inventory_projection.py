#!/usr/bin/env python3
"""Structural certification for Genesis UI-A4.1."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = [
    "core/integration/knowledge_inventory.py",
    "core/integration/providers/knowledge.py",
    "core/integration/providers/__init__.py",
    "core/integration/bootstrap.py",
    "tests/test_genesis_ui_a41_knowledge_inventory_projection.py",
    "docs/architecture/genesis_ui_a41_knowledge_inventory_projection.md",
    "docs/decisions/ADR-EXEC-0004-knowledge-inventory-projection.md",
    "docs/plans/genesis_ui_a41_completion_criteria.md",
]


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    for relative in REQUIRED_FILES:
        path = ROOT / relative

        if not path.is_file():
            fail(f"Missing required file: {relative}")

        if path.suffix == ".py":
            try:
                ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError as exc:
                fail(f"Syntax error in {relative}: {exc}")

    bootstrap = (
        ROOT / "core/integration/bootstrap.py"
    ).read_text(encoding="utf-8")

    required_bootstrap_tokens = (
        "KnowledgeInventoryService",
        "KnowledgeProjectionProvider",
        "projections.register(",
        "knowledge_inventory_service",
    )

    for token in required_bootstrap_tokens:
        if token not in bootstrap:
            fail(f"Bootstrap missing token: {token}")

    provider = (
        ROOT / "core/integration/providers/knowledge.py"
    ).read_text(encoding="utf-8")

    for token in (
        'projection_id = "knowledge"',
        "database_count",
        "database_total_rows",
        "total_files",
        "fingerprint",
    ):
        if token not in provider:
            fail(f"Knowledge provider missing token: {token}")

    inventory = (
        ROOT / "core/integration/knowledge_inventory.py"
    ).read_text(encoding="utf-8")

    for token in (
        "mode=ro",
        "JARVIS_KNOWLEDGE_ROOT",
        "JARVIS_KNOWLEDGE_PROJECTION_TTL_SECONDS",
        "JARVIS_KNOWLEDGE_SCAN_MAX_FILES",
    ):
        if token not in inventory:
            fail(f"Inventory service missing token: {token}")

    print("[PASS] Canonical UI-A4.1 file set")
    print("[PASS] Python syntax structure")
    print("[PASS] Read-only SQLite inventory boundary")
    print("[PASS] Knowledge projection contract")
    print("[PASS] Bootstrap registration structure")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
