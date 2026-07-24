#!/usr/bin/env python3
"""Structural verification for Phase X-C1."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REQUIRED = (
    ROOT / "core/representation/__init__.py",
    ROOT / "core/representation/contracts.py",
    ROOT / "core/representation/segmentation.py",
    ROOT / "tests/test_phase_xc1_cognitive_representation.py",
    ROOT / "docs/architecture/cognitive_representation_architecture.md",
)
FORBIDDEN = ("core.executive", "core.planning", "core.reasoning", "knowledge_engine")


def imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


def main() -> int:
    missing = [p for p in REQUIRED if not p.is_file()]
    if missing:
        for path in missing:
            print(f"[FAIL] Missing: {path.relative_to(ROOT)}")
        return 1

    for path in (ROOT / "core/representation/contracts.py", ROOT / "core/representation/segmentation.py"):
        for module in imports(path):
            if any(module == forbidden or module.startswith(forbidden + ".") for forbidden in FORBIDDEN):
                print(f"[FAIL] Forbidden dependency: {path.relative_to(ROOT)} -> {module}")
                return 1

    from core.representation import SegmentKind, segment_text

    sample = (
        "Operational Review\n\n"
        "Primary responded. Secondary offline.\n\n"
        "- Preserve evidence.\n- Escalate condition."
    )
    first = segment_text(artifact_id="verify", text=sample)
    second = segment_text(artifact_id="verify", text=sample)

    if first != second:
        print("[FAIL] Non-deterministic result.")
        return 1

    expected = (
        SegmentKind.HEADING,
        SegmentKind.SENTENCE,
        SegmentKind.SENTENCE,
        SegmentKind.BULLET,
        SegmentKind.BULLET,
    )
    if tuple(s.kind for s in first.segments) != expected:
        print("[FAIL] Unexpected segmentation.")
        return 1

    print("Phase X-C1 structural verification passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
