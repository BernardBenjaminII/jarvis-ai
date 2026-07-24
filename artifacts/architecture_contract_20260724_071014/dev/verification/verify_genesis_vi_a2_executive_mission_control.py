#!/usr/bin/env python3
"""Certification verifier for Genesis VI-A2 Executive Mission Control."""

from __future__ import annotations

import hashlib
import importlib
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FILES = (
    "core/src/routes/operations.py",
    "core/src/static/mission_control/index.html",
    "core/src/static/mission_control/styles.css",
    "core/src/static/mission_control/app.js",
    "tests/test_genesis_vi_a2_executive_mission_control.py",
    "docs/architecture/ui/genesis_vi_a2_executive_mission_control.md",
)


def report(name: str, passed: bool, detail: str = "") -> int:
    suffix = f" — {detail}" if detail else ""
    print(f"[{'PASS' if passed else 'FAIL'}] {name}{suffix}")
    return 0 if passed else 1


def main() -> int:
    failed = 0
    print("=" * 72)
    print("JARVIS — GENESIS VI-A2 EXECUTIVE MISSION CONTROL")
    print("=" * 72)

    missing = [path for path in FILES if not (ROOT / path).is_file()]
    failed += report("Canonical VI-A2 file set", not missing, ", ".join(missing) if missing else "complete")

    compile_result = subprocess.run(
        [sys.executable, "-m", "compileall", "-q", "core/src/routes/operations.py", "tests/test_genesis_vi_a2_executive_mission_control.py"],
        cwd=ROOT,
        check=False,
    )
    failed += report("Python compilation", compile_result.returncode == 0)

    try:
        module = importlib.import_module("core.src.routes.operations")
        route_ok = callable(getattr(module, "operations_executive", None))
        detail = "canonical /operations/executive projection"
    except Exception as exc:
        route_ok, detail = False, f"{type(exc).__name__}: {exc}"
    failed += report("Executive Operations route", route_ok, detail)

    javascript = (ROOT / "core/src/static/mission_control/app.js").read_text(encoding="utf-8")
    boundary_ok = "/operations/executive" in javascript and '"/executive/' not in javascript and '"/reasoning/' not in javascript
    failed += report("Operations-only browser boundary", boundary_ok)

    html = (ROOT / "core/src/static/mission_control/index.html").read_text(encoding="utf-8")
    telemetry_ok = all(token in html for token in ("pending-decisions", "pending-recommendations", "observations", "inferences", "plans"))
    failed += report("Executive telemetry surface", telemetry_ok)

    tests = subprocess.run(
        [sys.executable, "-m", "unittest", "-v", "tests.test_genesis_vi_a2_executive_mission_control", "tests.test_mc1001_operations", "tests.test_mc1002_commanders_bridge"],
        cwd=ROOT,
        check=False,
    )
    failed += report("VI-A2 and Mission Control regression", tests.returncode == 0)

    digest = hashlib.sha256()
    for relative in FILES:
        path = ROOT / relative
        if path.is_file():
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    failed += report("Deterministic architecture fingerprint", True, digest.hexdigest())

    print("-" * 72)
    print(f"Checks failed : {failed}")
    print(f"Overall status: {'EXCELLENT' if failed == 0 else 'FAILED'}")
    print("=" * 72)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
