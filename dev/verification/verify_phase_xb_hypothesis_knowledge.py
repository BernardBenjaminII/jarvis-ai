#!/usr/bin/env python3
"""Structural verification for Phase X-B."""

from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = (
    "core/reasoning/knowledge.py",
    "core/reasoning/generation.py",
    "core/reasoning/pipeline.py",
    "tests/test_phase_xb_hypothesis_knowledge.py",
    "docs/architecture/reasoning_hypothesis_knowledge_integration.md",
)
FORBIDDEN = (
    "knowledge_engine.storage",
    "knowledge_engine.director",
    "knowledge_engine.search.service",
    "subprocess",
    "openai",
)

def main() -> int:
    failures: list[str] = []
    for relative in REQUIRED:
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"Missing required file: {relative}")
            continue
        if path.suffix == ".py":
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError as exc:
                failures.append(f"Syntax error in {relative}: {exc}")
                continue
            for node in ast.walk(tree):
                module = None
                if isinstance(node, ast.ImportFrom):
                    module = node.module
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith(FORBIDDEN):
                            failures.append(
                                f"{relative} imports forbidden dependency {alias.name}"
                            )
                if module and module.startswith(FORBIDDEN):
                    failures.append(
                        f"{relative} imports forbidden dependency {module}"
                    )
    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1
    print("[PASS] Phase X-B structural boundaries are valid")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
