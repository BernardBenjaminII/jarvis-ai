from __future__ import annotations
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = (
    "core/src/static/mission_control/timeline_projection.js",
    "core/src/static/mission_control/timeline_projection.css",
    "core/src/static/mission_control/index.html",
    "tests/test_genesis_vii_a0_pack4b1_timeline_projection.py",
    "docs/genesis/genesis_vii_a0/GENESIS_VII_A0_PACK_4B_1.md",
)

def main() -> int:
    failures = 0
    for relative in REQUIRED:
        path = ROOT / relative
        if path.is_file() and path.stat().st_size > 0:
            print(f"[PASS] {relative}")
        else:
            print(f"[FAIL] {relative}")
            failures += 1

    node_result = subprocess.run(
        ["node", "--check", str(ROOT / "core/src/static/mission_control/timeline_projection.js")],
        check=False,
    )
    if node_result.returncode == 0:
        print("[PASS] JavaScript syntax")
    else:
        print("[FAIL] JavaScript syntax")
        failures += 1

    test_result = subprocess.run(
        [sys.executable, "-m", "unittest",
         "tests.test_genesis_vii_a0_pack4b1_timeline_projection", "-v"],
        cwd=ROOT,
        check=False,
    )
    if test_result.returncode == 0:
        print("[PASS] Timeline projection certification tests")
    else:
        print("[FAIL] Timeline projection certification tests")
        failures += 1

    print()
    print(f"Checks failed : {failures}")
    print("Overall status: " + ("EXCELLENT" if failures == 0 else "REQUIRES CORRECTION"))
    return 0 if failures == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())
