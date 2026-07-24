#!/usr/bin/env python3
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def check(condition: bool, label: str) -> int:
    print(f"[{'PASS' if condition else 'FAIL'}] {label}")
    return 0 if condition else 1

def main() -> int:
    failures = 0
    required = (
        ROOT / "core/engineering/__init__.py",
        ROOT / "core/engineering/constitution.py",
        ROOT / "core/engineering/contracts.py",
        ROOT / "core/engineering/enums.py",
        ROOT / "core/engineering/errors.py",
        ROOT / "docs/constitution/ENGINEERING_CONSTITUTION.md",
        ROOT / "docs/engineering/engineering_os_architecture.md",
        ROOT / "tests/test_genesis_5e0_engineering_os_foundation.py",
    )
    failures += check(all(path.is_file() for path in required), "Required Engineering OS files")

    result = subprocess.run(
        [sys.executable, "-m", "compileall", "-q", "core/engineering",
         "tests/test_genesis_5e0_engineering_os_foundation.py"],
        cwd=ROOT, check=False,
    )
    failures += check(result.returncode == 0, "Engineering OS compilation")

    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "core/engineering").glob("*.py")
    )
    failures += check("@dataclass(frozen=True, slots=True)" in source, "Immutable contracts")
    failures += check(
        "subprocess" not in source and "requests" not in source and "os.system" not in source,
        "No process, network, or source-write side effects",
    )
    failures += check(
        "from core.architecture import" in source,
        "Architecture Intelligence integration",
    )

    tests = subprocess.run(
        [sys.executable, "-m", "unittest", "-v",
         "tests.test_genesis_5e0_engineering_os_foundation"],
        cwd=ROOT, check=False,
    )
    failures += check(tests.returncode == 0, "Genesis V-E0 unit tests")

    smoke = (
        "from core.engineering import ENGINEERING_CONSTITUTION, constitution_fingerprint;"
        "a=constitution_fingerprint();b=constitution_fingerprint();"
        "assert a==b and len(a)==64 and len(ENGINEERING_CONSTITUTION)>=9;print(a)"
    )
    one = subprocess.run([sys.executable, "-c", smoke], cwd=ROOT, check=False,
                         capture_output=True, text=True)
    two = subprocess.run([sys.executable, "-c", smoke], cwd=ROOT, check=False,
                         capture_output=True, text=True)
    failures += check(
        one.returncode == 0 and two.returncode == 0 and one.stdout == two.stdout,
        "Deterministic Engineering Constitution fingerprint",
    )

    print()
    print("-" * 72)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 72)
    return 1 if failures else 0

if __name__ == "__main__":
    raise SystemExit(main())
