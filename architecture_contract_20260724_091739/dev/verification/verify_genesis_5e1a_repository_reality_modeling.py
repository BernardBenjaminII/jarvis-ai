#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def check(condition: bool, label: str) -> int:
    print(f"[{'PASS' if condition else 'FAIL'}] {label}")
    return 0 if condition else 1


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        check=False,
        capture_output=False,
        text=True,
    )


def main() -> int:
    failures = 0
    required = (
        ROOT / "core/engineering/inventory_targets.py",
        ROOT / "core/engineering/import_resolution.py",
        ROOT / "core/engineering/api_inventory.py",
        ROOT / "docs/engineering/genesis_v_e1a_repository_reality_modeling.md",
        ROOT / "tests/test_genesis_5e1a_repository_reality_modeling.py",
    )
    failures += check(all(path.is_file() for path in required), "V-E1A required files")
    failures += check(
        run(
            "-m",
            "compileall",
            "-q",
            "core/engineering",
            "tests/test_genesis_5e1a_repository_reality_modeling.py",
        ).returncode == 0,
        "V-E1A compilation",
    )
    failures += check(
        run(
            "-m",
            "unittest",
            "-v",
            "tests.test_genesis_5e1a_repository_reality_modeling",
        ).returncode == 0,
        "V-E1A unit tests",
    )

    source = (
        (ROOT / "core/engineering/import_resolution.py").read_text(encoding="utf-8")
        + (ROOT / "core/engineering/api_inventory.py").read_text(encoding="utf-8")
    )
    failures += check(
        "importlib" not in source
        and "subprocess" not in source
        and "exec(" not in source
        and "eval(" not in source,
        "Static non-executing resolution boundary",
    )

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        core = root / "core"
        pkg = core / "pkg"
        core.mkdir()
        pkg.mkdir()
        (core / "__init__.py").write_text("", encoding="utf-8")
        (core / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
        (pkg / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
        smoke = (
            "from pathlib import Path;"
            "from core.engineering import PythonImportResolver;"
            f"r=Path({str(root)!r});x=PythonImportResolver(r);"
            "a=x.resolve('core.module');b=x.resolve('core.pkg');"
            "c=x.resolve('core.missing');"
            "assert a.target.kind=='module';"
            "assert b.target.kind=='package';"
            "assert c.target.kind=='missing';"
            "print(a.fingerprint(),b.fingerprint(),c.fingerprint())"
        )
        first = subprocess.run(
            [sys.executable, "-c", smoke],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        second = subprocess.run(
            [sys.executable, "-c", smoke],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        failures += check(
            first.returncode == 0
            and second.returncode == 0
            and first.stdout == second.stdout,
            "Deterministic target resolution",
        )

    failures += check(
        run("dev/verification/verify_genesis_5e1_public_api_compatibility.py").returncode == 0,
        "Genesis V-E1 regression",
    )
    failures += check(
        run("dev/verification/verify_genesis_5e0_engineering_os_foundation.py").returncode == 0,
        "Genesis V-E0 regression",
    )

    print()
    print("-" * 72)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 72)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
