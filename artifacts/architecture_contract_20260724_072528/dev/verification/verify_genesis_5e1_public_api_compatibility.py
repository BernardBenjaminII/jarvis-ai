#!/usr/bin/env python3
"""Verify Genesis V-E1 Public API Compatibility Intelligence."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def check(condition: bool, label: str) -> int:
    print(f"[{'PASS' if condition else 'FAIL'}] {label}")
    return 0 if condition else 1


def main() -> int:
    failures = 0

    required = (
        ROOT / "core/engineering/api_inventory.py",
        ROOT / "core/engineering/compatibility.py",
        ROOT / "core/engineering/restoration.py",
        ROOT / "core/engineering/reporting.py",
        ROOT / "core/engineering/cli.py",
        ROOT / "docs/engineering/genesis_v_e1_public_api_compatibility.md",
        ROOT / "tests/test_genesis_5e1_public_api_compatibility.py",
    )
    failures += check(all(path.is_file() for path in required), "V-E1 required files")

    compile_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "compileall",
            "-q",
            "core/engineering",
            "tests/test_genesis_5e1_public_api_compatibility.py",
        ],
        cwd=ROOT,
        check=False,
    )
    failures += check(compile_result.returncode == 0, "V-E1 compilation")

    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            ROOT / "core/engineering/api_inventory.py",
            ROOT / "core/engineering/compatibility.py",
            ROOT / "core/engineering/restoration.py",
            ROOT / "core/engineering/reporting.py",
        )
    )
    failures += check("ast.parse" in source, "Static AST inventory")
    failures += check(
        "importlib" not in source
        and "subprocess" not in source
        and "os.system" not in source
        and "requests" not in source,
        "Analyzer has no runtime import, process, or network authority",
    )

    unit_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "-v",
            "tests.test_genesis_5e1_public_api_compatibility",
        ],
        cwd=ROOT,
        check=False,
    )
    failures += check(unit_result.returncode == 0, "V-E1 unit tests")

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        package = root / "core" / "fixture"
        tests = root / "tests"
        package.mkdir(parents=True)
        tests.mkdir()
        (root / "core/__init__.py").write_text("", encoding="utf-8")
        (package / "__init__.py").write_text(
            'from .contracts import Present\n__all__ = ["Present"]\n',
            encoding="utf-8",
        )
        (package / "contracts.py").write_text(
            "class Present:\n    pass\nclass Hidden:\n    pass\n",
            encoding="utf-8",
        )
        (tests / "test_api.py").write_text(
            "from core.fixture import Present, Hidden\n",
            encoding="utf-8",
        )

        smoke = (
            "from pathlib import Path;"
            "from core.engineering import expectations_from_tests,inventory_package,"
            "analyze_compatibility,build_restoration_plan;"
            f"r=Path({str(root)!r});"
            "e=expectations_from_tests(r,r/'tests');"
            "i=inventory_package(r,'core.fixture');"
            "a=analyze_compatibility(e,(i,));"
            "p=build_restoration_plan(a);"
            "assert a.compatibility_score==0.5;"
            "assert p[0].action=='restore_public_export';"
            "print(a.fingerprint())"
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
            "Deterministic compatibility smoke test",
        )

    genesis_v_e0 = subprocess.run(
        [sys.executable, "dev/verification/verify_genesis_5e0_engineering_os_foundation.py"],
        cwd=ROOT,
        check=False,
    )
    failures += check(genesis_v_e0.returncode == 0, "Genesis V-E0 regression")

    print()
    print("-" * 72)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 72)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
