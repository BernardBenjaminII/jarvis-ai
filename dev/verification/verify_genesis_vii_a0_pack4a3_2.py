"""Verify Genesis VII-A0 Pack 4A-3.2."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = (
    "core/executive/timeline/locking.py",
    "core/executive/timeline/storage.py",
    "core/executive/timeline/repository.py",
    "core/executive/events/bus.py",
    "core/executive/events/runtime.py",
    "tests/test_genesis_vii_a0_pack4a3_1_publisher_wiring.py",
    "tests/test_genesis_vii_a0_pack4a3_2_concurrency_safety.py",
    "dev/tools/executive_timeline_recover.py",
    "docs/genesis/genesis_vii_a0/GENESIS_VII_A0_PACK_4A_3_2.md",
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

    repository_text = (
        ROOT / "core/executive/timeline/repository.py"
    ).read_text(encoding="utf-8")

    contracts = (
        "_read_disk_events_unlocked",
        "with self._storage.exclusive():",
        "append_many_unlocked",
    )
    missing = [
        contract
        for contract in contracts
        if contract not in repository_text
    ]
    if missing:
        print(
            "[FAIL] Repository transaction contract: "
            + ", ".join(missing)
        )
        failures += 1
    else:
        print("[PASS] Repository transaction contract")

    compile_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "py_compile",
            *(str(ROOT / item) for item in REQUIRED
              if item.endswith(".py")),
        ],
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
            "tests.test_genesis_vii_a0_pack4a2_publishers",
            "tests.test_genesis_vii_a0_pack4a3_runtime_bootstrap",
            "tests.test_genesis_vii_a0_pack4a3_1_publisher_wiring",
            "tests.test_genesis_vii_a0_pack4a3_2_concurrency_safety",
            "-v",
        ],
        cwd=ROOT,
        check=False,
    )
    if test_result.returncode == 0:
        print("[PASS] Pack 4A concurrency regression")
    else:
        print("[FAIL] Pack 4A concurrency regression")
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
