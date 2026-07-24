#!/usr/bin/env python3
"""Verification for Genesis VI-A3 cognitive state machine."""

from __future__ import annotations

import ast
import hashlib
import importlib
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, List, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

REQUIRED_FILES = (
    "core/cognition/__init__.py",
    "core/cognition/enums.py",
    "core/cognition/errors.py",
    "core/cognition/models.py",
    "core/cognition/working_memory.py",
    "core/cognition/state_machine.py",
    "tests/test_genesis_vi_a1_step1_foundation.py",
    "tests/test_genesis_vi_a2_working_memory.py",
    "tests/test_genesis_vi_a3_cognitive_state_machine.py",
    "docs/architecture/cognition/genesis_vi_a1_step1_foundation.md",
    "docs/architecture/cognition/genesis_vi_a2_working_memory.md",
    "docs/architecture/cognition/genesis_vi_a3_cognitive_state_machine.md",
)

FORBIDDEN_IMPORT_PREFIXES = (
    "openai",
    "anthropic",
    "ollama",
    "transformers",
    "langchain",
    "llama_index",
    "requests",
    "httpx",
)

EXPECTED_PUBLIC_SYMBOLS = (
    "CognitiveStateMachine",
    "DEFAULT_TRANSITION_POLICY",
    "StateMachineSnapshot",
    "TransitionGuard",
    "TransitionPolicy",
)

EXPECTED_FINGERPRINT = "9dc59b893564ba4aaa99386ff7379910862c4dd34d62111dd63dc8b75a1f90f2"


def check_required_files() -> Tuple[bool, str]:
    missing = [
        path for path in REQUIRED_FILES
        if not (PROJECT_ROOT / path).is_file()
    ]
    if missing:
        return False, f"Missing required files: {missing}"
    return True, "Canonical Genesis VI-A3 file structure"


def check_compilation() -> Tuple[bool, str]:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "compileall",
            "-q",
            str(PROJECT_ROOT / "core" / "cognition"),
            str(PROJECT_ROOT / "tests" / "test_genesis_vi_a3_cognitive_state_machine.py"),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return False, result.stderr.strip() or result.stdout.strip()
    return True, "Genesis VI-A3 package compilation"


def imported_modules(path: Path) -> List[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def check_dependency_isolation() -> Tuple[bool, str]:
    violations: List[str] = []
    for path in sorted((PROJECT_ROOT / "core" / "cognition").glob("*.py")):
        for module in imported_modules(path):
            if module.startswith(FORBIDDEN_IMPORT_PREFIXES):
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)} -> {module}"
                )
    if violations:
        return False, f"Forbidden cognition dependencies: {violations}"
    return True, "Vendor, model, network, and retrieval isolation"


def check_public_imports() -> Tuple[bool, str]:
    module = importlib.import_module("core.cognition")
    missing = [
        symbol for symbol in module.__all__
        if not hasattr(module, symbol)
    ]
    missing.extend(
        symbol for symbol in EXPECTED_PUBLIC_SYMBOLS
        if not hasattr(module, symbol)
    )
    if missing:
        return False, f"Missing public symbols: {sorted(set(missing))}"
    return True, "Stable Genesis VI-A3 public imports"


def run_unittest(module_name: str, label: str) -> Tuple[bool, str]:
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "-v", module_name],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        output = "\n".join(
            part for part in (result.stdout.strip(), result.stderr.strip())
            if part
        )
        return False, output
    return True, label


def check_unit_tests() -> Tuple[bool, str]:
    return run_unittest(
        "tests.test_genesis_vi_a3_cognitive_state_machine",
        "Genesis VI-A3 cognitive-state-machine unit tests",
    )


def check_a2_regression() -> Tuple[bool, str]:
    return run_unittest(
        "tests.test_genesis_vi_a2_working_memory",
        "Genesis VI-A2 regression",
    )


def check_a1_regression() -> Tuple[bool, str]:
    return run_unittest(
        "tests.test_genesis_vi_a1_step1_foundation",
        "Genesis VI-A1 Step 1 regression",
    )


class DeterministicClock:
    def __init__(self) -> None:
        self._value = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        value = self._value
        self._value += timedelta(seconds=1)
        return value


def deterministic_smoke_fingerprint() -> str:
    from core.cognition import CognitiveState, CognitiveStateMachine

    machine = CognitiveStateMachine(clock=DeterministicClock())
    machine.transition_path(
        (
            CognitiveState.INITIALIZING,
            CognitiveState.OBSERVING,
            CognitiveState.ATTENDING,
            CognitiveState.RETRIEVING,
            CognitiveState.REASONING,
            CognitiveState.EVALUATING,
            CognitiveState.PLANNING,
            CognitiveState.EXECUTING,
            CognitiveState.REFLECTING,
            CognitiveState.COMPLETED,
        ),
        reason_prefix="Genesis VI-A3 certification",
    )

    payload = "|".join(
        [
            machine.current_state.value,
            ",".join(
                f"{item.sequence}:{item.previous_state.value}>{item.next_state.value}"
                for item in machine.transitions()
            ),
            ",".join(
                f"{event.sequence}:{event.kind.value}:{event.state.value}"
                for event in machine.events()
            ),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def check_deterministic_smoke() -> Tuple[bool, str]:
    fingerprint = deterministic_smoke_fingerprint()
    if fingerprint != EXPECTED_FINGERPRINT:
        return (
            False,
            "Deterministic smoke fingerprint mismatch: "
            f"expected {EXPECTED_FINGERPRINT}, got {fingerprint}",
        )
    return True, "Deterministic cognitive-lifecycle smoke fingerprint"


def run_check(
    check: Callable[[], Tuple[bool, str]],
) -> Tuple[bool, str]:
    try:
        return check()
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def main() -> int:
    print()
    print("=" * 72)
    print("JARVIS — GENESIS VI-A3 COGNITIVE STATE MACHINE")
    print("=" * 72)

    checks = (
        check_required_files,
        check_compilation,
        check_dependency_isolation,
        check_public_imports,
        check_unit_tests,
        check_a2_regression,
        check_a1_regression,
        check_deterministic_smoke,
    )

    failures = 0
    for check in checks:
        passed, detail = run_check(check)
        print(f"[{'PASS' if passed else 'FAIL'}] {detail}")
        if not passed:
            failures += 1

    print("-" * 72)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 72)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
