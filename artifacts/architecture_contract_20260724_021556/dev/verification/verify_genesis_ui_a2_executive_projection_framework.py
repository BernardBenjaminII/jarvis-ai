#!/usr/bin/env python3
from __future__ import annotations
import ast
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
REQUIRED = [
"core/integration/__init__.py", "core/integration/bootstrap.py", "core/integration/contracts.py",
"core/integration/errors.py", "core/integration/provider.py", "core/integration/registry.py",
"core/integration/service.py", "core/integration/providers/__init__.py",
"core/integration/providers/capabilities.py", "core/integration/providers/operations.py",
"core/src/routes/operations.py", "tests/test_genesis_ui_a2_executive_projection_framework.py"]
def main():
    for rel in REQUIRED:
        path=ROOT/rel
        if not path.is_file(): raise SystemExit(f"[FAIL] Missing required file: {rel}")
        if path.suffix==".py": ast.parse(path.read_text(encoding="utf-8"))
    source=(ROOT/"core/src/routes/operations.py").read_text(encoding="utf-8")
    for route in ['"/projections"','"/projections/{projection_id}"','"/capabilities"','"/capabilities/{capability_name}"']:
        if route not in source: raise SystemExit(f"[FAIL] Missing route: {route}")
    print("[PASS] Canonical UI-A2 file set")
    print("[PASS] Python syntax structure")
    print("[PASS] Projection and capability route structure")
    return 0
if __name__ == "__main__": raise SystemExit(main())
