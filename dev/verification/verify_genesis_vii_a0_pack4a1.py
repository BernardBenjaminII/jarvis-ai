"""Verify Genesis VII-A0 Pack 4A-1."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
REQUIRED_FILES = (
    "core/executive/events/__init__.py",
    "core/executive/events/bus.py",
    "core/executive/events/contracts.py",
    "core/executive/events/integration.py",
    "core/executive/events/runtime.py",
    "core/executive/timeline/engine.py",
    "tests/test_genesis_vii_a0_pack4a1_event_bus.py",
    "docs/genesis/genesis_vii_a0/GENESIS_VII_A0_PACK_4A_1.md",
)


def main() -> int:
    failures = 0
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        if path.is_file() and path.stat().st_size > 0:
            print(f"[PASS] {relative}")
        else:
            print(f"[FAIL] {relative}")
            failures += 1

    python_files = [
        str(ROOT / relative)
        for relative in REQUIRED_FILES
        if relative.endswith(".py")
    ]
    compile_result = subprocess.run(
        [sys.executable, "-m", "py_compile", *python_files],
        check=False,
    )
    if compile_result.returncode == 0:
        print("[PASS] Python compilation")
    else:
        print("[FAIL] Python compilation")
        failures += 1

    test_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "tests.test_genesis_vii_a0_pack4a1_event_bus",
            "-v",
        ],
        cwd=ROOT,
        check=False,
    )
    if test_result.returncode == 0:
        print("[PASS] Event Bus certification tests")
    else:
        print("[FAIL] Event Bus certification tests")
        failures += 1

    print()
    print(f"Checks failed : {failures}")
    print(
        "Overall status: "
        + ("EXCELLENT" if failures == 0 else "REQUIRES CORRECTION")
    )
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
