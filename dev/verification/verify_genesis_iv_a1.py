#!/usr/bin/env python3
from __future__ import annotations
import hashlib, py_compile, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
FILES=("core/cognition/observation/__init__.py","core/cognition/observation/enums.py",
"core/cognition/observation/errors.py","core/cognition/observation/models.py",
"core/cognition/observation/repository.py","core/cognition/observation/bus.py",
"core/cognition/observation/service.py","tests/test_genesis_iv_a1_executive_observation_bus.py",
"docs/architecture/genesis_iv_a1_executive_observation_bus.md",
"docs/decisions/ADR-0026-executive-observation-bus.md","dev/verify_genesis_4a1.sh")

def main():
    print("="*72); print("JARVIS — GENESIS IV-A1 EXECUTIVE OBSERVATION BUS"); print("="*72)
    missing=[x for x in FILES if not (ROOT/x).is_file()]
    if missing: raise SystemExit(f"[FAIL] Missing files: {missing}")
    print("[PASS] Canonical IV-A1 file set")
    for x in FILES:
        if x.endswith(".py"): py_compile.compile(str(ROOT/x),doraise=True)
    print("[PASS] Python compilation")
    result=subprocess.run([sys.executable,"-m","unittest","-v","tests.test_genesis_iv_a1_executive_observation_bus"],cwd=ROOT)
    if result.returncode: raise SystemExit("[FAIL] Unit tests")
    print("[PASS] Genesis IV-A1 unit tests")
    digest=hashlib.sha256()
    for x in sorted(f for f in FILES if f.startswith("core/")): digest.update((ROOT/x).read_bytes())
    print("[INFO] Architecture fingerprint:",digest.hexdigest())
    print("Checks failed : 0"); print("Overall status: EXCELLENT"); print("="*72)

if __name__=="__main__": main()
