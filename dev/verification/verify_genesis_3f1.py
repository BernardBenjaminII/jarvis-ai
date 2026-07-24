#!/usr/bin/env python3
from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = (
    "dev/tools/audit_genesis_3f1.py",
    "dev/verification/verify_genesis_3f1.py",
    "dev/verify_genesis_3f1.sh",
    "tests/test_genesis_3f1_integration_freeze.py",
    "docs/architecture/genesis_3f1_cognitive_workspace_integration_freeze.md",
    "docs/decisions/ADR-0025-genesis-iii-integration-freeze.md",
    "docs/architecture/convergence/genesis_3f1_public_api.json",
    "docs/architecture/convergence/genesis_3f1_public_api.md",
    "docs/architecture/convergence/genesis_3f1_dependency_graph.json",
    "docs/architecture/convergence/genesis_3f1_dependency_graph.md",
    "docs/architecture/convergence/genesis_3f1_snapshot.json",
    "docs/architecture/convergence/genesis_3f1_executive_readiness.md",
)


def main() -> int:
    missing = [path for path in REQUIRED if not (ROOT / path).is_file()]
    if missing:
        print("[FAIL] Missing Genesis III-F1 files:")
        for path in missing:
            print(f"  - {path}")
        return 1
    print("[PASS] Genesis III-F1 required files exist")

    for relative in REQUIRED:
        if relative.endswith(".py"):
            ast.parse((ROOT / relative).read_text(encoding="utf-8"), filename=relative)
    print("[PASS] Genesis III-F1 Python sources parse")

    snapshot_path = ROOT / "docs/architecture/convergence/genesis_3f1_snapshot.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    fingerprint = snapshot.get("architecture_fingerprint", "")
    if not isinstance(fingerprint, str) or len(fingerprint) != 64:
        print("[FAIL] Invalid architecture fingerprint")
        return 1
    if snapshot.get("schema") != "genesis-3f0/v1":
        print("[FAIL] Unexpected snapshot schema")
        return 1
    if snapshot.get("dependency_graph", {}).get("violations"):
        print("[FAIL] Snapshot records dependency violations")
        return 1
    print(f"[PASS] Certified architecture fingerprint: {fingerprint}")
    print("[PASS] Genesis III-F1 snapshot structure")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
