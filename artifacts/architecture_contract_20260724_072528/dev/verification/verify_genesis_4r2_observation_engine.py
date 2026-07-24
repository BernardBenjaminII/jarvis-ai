#!/usr/bin/env python3
from __future__ import annotations

import ast
import importlib
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = PROJECT_ROOT / "core/cognition/layers/observation"

# Directly executed scripts normally place dev/verification on sys.path rather
# than the repository root. Bootstrap the repository explicitly so imports such
# as core.cognition... work regardless of the caller's current directory.
project_root_text = str(PROJECT_ROOT)
if project_root_text not in sys.path:
    sys.path.insert(0, project_root_text)


REQUIRED_MODULES = (
    "__init__.py",
    "conflicts.py",
    "director.py",
    "duplicates.py",
    "enums.py",
    "errors.py",
    "factory.py",
    "lifecycle.py",
    "merge.py",
    "models.py",
    "normalization.py",
    "query.py",
    "registry.py",
    "relationships.py",
    "validation.py",
)


def passed(message: str) -> None:
    print(f"[PASS] {message}")


def failed(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def verify_runtime_context() -> None:
    if not PROJECT_ROOT.is_dir():
        failed(f"Project root does not exist: {PROJECT_ROOT}")

    if not (PROJECT_ROOT / "core").is_dir():
        failed(f"Core package directory is missing: {PROJECT_ROOT / 'core'}")

    if sys.path[0] != project_root_text:
        failed("Project root was not placed first on sys.path")

    passed("Repository-native Python import context")


def verify_structure() -> None:
    missing = [
        name
        for name in REQUIRED_MODULES
        if not (PACKAGE_ROOT / name).is_file()
    ]

    if missing:
        failed(f"Missing production modules: {', '.join(missing)}")

    passed("Canonical Observation Engine package")


def verify_prerequisites() -> None:
    prerequisites = (
        PROJECT_ROOT / "core/cognition/common/__init__.py",
        PROJECT_ROOT / "core/cognition/common/object_model.py",
    )

    missing = [
        str(path.relative_to(PROJECT_ROOT))
        for path in prerequisites
        if not path.is_file()
    ]

    if missing:
        failed(f"Missing Genesis IV-R1 prerequisites: {', '.join(missing)}")

    passed("Genesis IV-R1 cognition prerequisites")


def verify_import_boundaries() -> None:
    forbidden = (
        "core.cognition.layers.evidence",
        "core.cognition.layers.claims",
        "core.cognition.layers.hypotheses",
        "core.cognition.layers.interpretation",
        "core.cognition.layers.justification",
        "core.cognition.layers.reasoning",
        "core.reasoning",
        "core.executive",
        "api",
        "ui",
    )

    violations: list[str] = []

    for path in sorted(PACKAGE_ROOT.glob("*.py")):
        tree = ast.parse(
            path.read_text(encoding="utf-8"),
            filename=str(path),
        )

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.startswith(forbidden):
                    violations.append(f"{path.name}: {module}")

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(forbidden):
                        violations.append(f"{path.name}: {alias.name}")

    if violations:
        failed("Forbidden dependencies: " + "; ".join(violations))

    passed("Forward-only cognition dependency boundaries")


def verify_public_imports() -> None:
    module = importlib.import_module(
        "core.cognition.layers.observation"
    )

    required = (
        "ObservationDirector",
        "ObservationFactory",
        "ObservationInput",
        "ObservationLifecycleManager",
        "ObservationRecord",
        "ObservationRegistry",
        "ObservationValidator",
    )

    missing = [
        name
        for name in required
        if not hasattr(module, name)
    ]

    if missing:
        failed(f"Missing public exports: {', '.join(missing)}")

    passed("Stable Observation Engine public imports")


def run_command(
    command: list[str],
    *,
    failure_message: str,
    success_message: str,
) -> None:
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env={
            **dict(__import__("os").environ),
            "PYTHONPATH": project_root_text,
        },
        check=False,
    )

    if result.returncode != 0:
        failed(failure_message)

    passed(success_message)


def run_tests() -> None:
    run_command(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            str(PROJECT_ROOT / "tests/cognition"),
            "-t",
            str(PROJECT_ROOT),
            "-p",
            "test_genesis_4r2_*.py",
        ],
        failure_message="Genesis IV-R2 unit tests",
        success_message="Genesis IV-R2 unit tests",
    )


def run_cognition_regression() -> None:
    run_command(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            str(PROJECT_ROOT / "tests/cognition"),
            "-t",
            str(PROJECT_ROOT),
            "-p",
            "test_*.py",
        ],
        failure_message="Cognition regression suite",
        success_message="Cognition regression suite",
    )


def smoke_test() -> None:
    from core.cognition.common.object_model import ProvenanceReference
    from core.cognition.layers.observation import (
        ObservationDirector,
        ObservationInput,
        ObservationLifecycleState,
        ObservationSourceMode,
    )

    director = ObservationDirector()

    observation = director.observe(
        ObservationInput(
            content="Genesis IV-R2 deterministic smoke observation.",
            subject="genesis-4r2",
            source_mode=ObservationSourceMode.SYSTEM,
            provenance=(
                ProvenanceReference(
                    source_id="genesis-4r2-verifier",
                    source_type="system",
                ),
            ),
        )
    )

    retrieved = director.get(observation.observation_id)

    if retrieved != observation:
        failed("Observation registry retrieval mismatch")

    if observation.lifecycle_state != ObservationLifecycleState.ACTIVE:
        failed("Observed record was not activated")

    if len(observation.deterministic_hash) != 64:
        failed("Observation deterministic hash is invalid")

    passed("Deterministic Observation Director smoke test")


def main() -> int:
    print("=" * 70)
    print("JARVIS GENESIS IV-R2 — OBSERVATION ENGINE")
    print("=" * 70)

    verify_runtime_context()
    verify_structure()
    verify_prerequisites()
    verify_import_boundaries()
    verify_public_imports()
    run_tests()
    run_cognition_regression()
    smoke_test()

    print("-" * 70)
    print("Checks failed  : 0")
    print("Overall status : EXCELLENT")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
