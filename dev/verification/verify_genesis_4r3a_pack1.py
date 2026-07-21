#!/usr/bin/env python3
"""Structural verification for Genesis IV-R3A Pack 1."""

from __future__ import annotations

import ast
import importlib
import subprocess
import sys
from pathlib import Path
from typing import Callable


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

PACKAGE_ROOT = PROJECT_ROOT / "core" / "evidence"
TEST_FILE = (
    PROJECT_ROOT
    / "tests"
    / "test_genesis_4r3a_pack1_evidence_foundation.py"
)

Check = tuple[str, Callable[[], None]]


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def check_required_files() -> None:
    required = (
        PACKAGE_ROOT / "__init__.py",
        PACKAGE_ROOT / "enums.py",
        PACKAGE_ROOT / "errors.py",
        TEST_FILE,
        PROJECT_ROOT / "dev" / "verify_genesis_4r3a_pack1.sh",
    )
    missing = [str(path.relative_to(PROJECT_ROOT)) for path in required if not path.is_file()]
    assert_true(not missing, f"Missing required files: {missing}")


def check_python_compilation() -> None:
    files = [
        PACKAGE_ROOT / "__init__.py",
        PACKAGE_ROOT / "enums.py",
        PACKAGE_ROOT / "errors.py",
        TEST_FILE,
        Path(__file__).resolve(),
    ]
    command = [sys.executable, "-m", "py_compile", *(str(path) for path in files)]
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def check_importability() -> None:
    module = importlib.import_module("core.evidence")
    assert_true(hasattr(module, "EvidenceDirection"), "EvidenceDirection not exported.")
    assert_true(hasattr(module, "EvidenceError"), "EvidenceError not exported.")


def check_no_reverse_observation_dependency() -> None:
    observation_root = PROJECT_ROOT / "core" / "observation"
    if not observation_root.exists():
        observation_root = PROJECT_ROOT / "core" / "observations"

    if not observation_root.exists():
        return

    violations: list[str] = []
    for path in observation_root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue

            if any(
                name == "core.evidence" or name.startswith("core.evidence.")
                for name in names
            ):
                violations.append(str(path.relative_to(PROJECT_ROOT)))

    assert_true(
        not violations,
        "Observation layer must not import Evidence Engine: "
        + ", ".join(sorted(set(violations))),
    )


def check_pack1_scope_boundary() -> None:
    allowed = {"__init__.py", "enums.py", "errors.py"}
    actual = {
        path.name
        for path in PACKAGE_ROOT.glob("*.py")
        if path.name != "__pycache__"
    }

    unexpected = actual - allowed
    assert_true(
        not unexpected,
        "Pack 1 contains future-phase modules: "
        + ", ".join(sorted(unexpected)),
    )


def check_no_runtime_services() -> None:
    prohibited_names = {
        "EvidenceService",
        "EvidenceRecord",
        "EvidenceSet",
        "Proposition",
        "WeightBreakdown",
    }

    discovered: set[str] = set()
    for path in (PACKAGE_ROOT / "__init__.py", PACKAGE_ROOT / "enums.py", PACKAGE_ROOT / "errors.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                discovered.add(node.name)

    overlap = prohibited_names & discovered
    assert_true(
        not overlap,
        f"Pack 1 introduced prohibited future symbols: {sorted(overlap)}",
    )


def check_unit_tests() -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "tests.test_genesis_4r3a_pack1_evidence_foundation",
            "-v",
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )


def main() -> int:
    checks: tuple[Check, ...] = (
        ("Required Pack 1 files", check_required_files),
        ("Pack 1 Python compilation", check_python_compilation),
        ("Stable evidence imports", check_importability),
        ("Observation-to-evidence dependency direction", check_no_reverse_observation_dependency),
        ("Pack 1 scope boundary", check_pack1_scope_boundary),
        ("No premature runtime contracts or services", check_no_runtime_services),
        ("Pack 1 unit tests", check_unit_tests),
    )

    failures = 0

    print()
    print("=" * 70)
    print("JARVIS GENESIS IV-R3A — EVIDENCE FOUNDATION PACK 1")
    print("=" * 70)

    for label, check in checks:
        try:
            check()
        except Exception as exc:  # noqa: BLE001 - verifier must report all failures
            failures += 1
            print(f"[FAIL] {label}")
            print(f"       {type(exc).__name__}: {exc}")
        else:
            print(f"[PASS] {label}")

    print("-" * 70)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 70)

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
