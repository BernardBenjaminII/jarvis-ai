#!/usr/bin/env python3
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES = (
    "core/cognition/integration/__init__.py",
    "core/cognition/integration/contracts.py",
    "core/cognition/integration/director.py",
    "core/cognition/integration/errors.py",
    "core/cognition/integration/models.py",
    "core/cognition/integration/pipeline.py",
    "core/cognition/integration/service.py",
    "tests/test_genesis_3a4_cognitive_workspace_integration.py",
    "docs/architecture/genesis_3a4_cognitive_workspace_integration.md",
    "docs/decisions/ADR-0024-cognitive-workspace-integration-engine.md",
)


def main() -> int:
    missing = [path for path in FILES if not (ROOT / path).is_file()]
    if missing:
        print("[FAIL] Missing files:", *missing, sep="\n  - ")
        return 1
    print("[PASS] Genesis III-A4 required files exist")

    for relative in FILES:
        if relative.endswith(".py"):
            ast.parse((ROOT / relative).read_text(encoding="utf-8"), filename=relative)
    print("[PASS] Genesis III-A4 Python sources parse")

    payload = {
        path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        for path in sorted(FILES)
    }
    fingerprint = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    print(f"[PASS] Deterministic architecture fingerprint: {fingerprint}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
