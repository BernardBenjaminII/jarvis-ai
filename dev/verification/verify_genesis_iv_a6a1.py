#!/usr/bin/env python3
from __future__ import annotations

import hashlib, py_compile, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = (
    "core/cognition/decision/__init__.py",
    "core/cognition/decision/contracts.py",
    "core/cognition/decision/enums.py",
    "core/cognition/decision/errors.py",
    "core/cognition/decision/models.py",
    "core/cognition/decision/synthesizer.py",
    "core/cognition/decision/repository.py",
    "core/cognition/decision/service.py",
    "tests/test_genesis_iv_a6a1_executive_decision_foundation.py",
    "docs/architecture/genesis_iv_a6a1_executive_decision_foundation.md",
    "docs/decisions/ADR-0031-executive-decision-boundary.md",
    "dev/verify_genesis_4a6a1.sh",
)

def main() -> int:
    print("=" * 72)
    print("JARVIS — GENESIS IV-A6.1 EXECUTIVE DECISION FOUNDATION")
    print("=" * 72)
    failed = 0
    missing = [p for p in REQUIRED if not (ROOT / p).is_file()]
    if missing:
        print(f"[FAIL] Canonical file set: {missing}"); failed += 1
    else:
        print("[PASS] Canonical IV-A6.1 file set")

    try:
        import core.cognition.reasoner as r
        assert hasattr(r, "ExecutiveReasoningResult")
        print("[PASS] Genesis IV-A5 prerequisite compatibility")
    except Exception as exc:
        print(f"[FAIL] Genesis IV-A5 prerequisite compatibility: {exc}"); failed += 1

    try:
        for p in REQUIRED:
            if p.endswith(".py"):
                py_compile.compile(str(ROOT / p), doraise=True)
        print("[PASS] Python compilation")
    except Exception as exc:
        print(f"[FAIL] Python compilation: {exc}"); failed += 1

    result = subprocess.run(
        [sys.executable, "-m", "unittest", "-v",
         "tests.test_genesis_iv_a6a1_executive_decision_foundation"],
        cwd=ROOT,
    )
    if result.returncode == 0:
        print("[PASS] Genesis IV-A6.1 unit tests")
    else:
        print("[FAIL] Genesis IV-A6.1 unit tests"); failed += 1

    manifest = ROOT / "dev/verification/manifests/genesis.manifest"
    if manifest.exists() and "dev/verify_genesis_4a6a1.sh" not in manifest.read_text():
        print("[FAIL] Constitutional Genesis manifest registration"); failed += 1
    else:
        print("[PASS] Constitutional Genesis manifest registration")

    digest = hashlib.sha256()
    for p in sorted(x for x in REQUIRED if x.startswith("core/")):
        digest.update((ROOT / p).read_bytes())
    print(f"[INFO] Architecture fingerprint: {digest.hexdigest()}")
    print("-" * 72)
    print(f"Checks failed : {failed}")
    print("Overall status: " + ("EXCELLENT" if failed == 0 else "FAILED"))
    print("=" * 72)
    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())
