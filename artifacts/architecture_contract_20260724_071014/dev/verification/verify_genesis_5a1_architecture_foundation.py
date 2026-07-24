#!/usr/bin/env python3
"""Verify Genesis V-A1 Architecture Intelligence Foundation."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = (
    ROOT / "core" / "architecture" / "__init__.py",
    ROOT / "core" / "architecture" / "contracts.py",
    ROOT / "core" / "architecture" / "enums.py",
    ROOT / "core" / "architecture" / "errors.py",
    ROOT / "core" / "architecture" / "fingerprints.py",
    ROOT / "docs" / "architecture" / "architecture_intelligence.md",
    ROOT / "tests" / "test_genesis_5a1_architecture_foundation.py",
)

REQUIRED_EXPORTS = {
    "ArchitectureFinding",
    "ArchitectureSnapshot",
    "CertificationRecord",
    "CompatibilityAssessment",
    "DependencyEdge",
    "MigrationPlan",
    "MigrationStep",
    "ModuleDefinition",
    "OwnershipDeclaration",
    "PublicSymbol",
    "SubsystemDefinition",
    "architecture_fingerprint",
    "canonical_json",
    "canonicalize",
    "file_fingerprint",
}


def check(condition: bool, label: str) -> int:
    if condition:
        print(f"[PASS] {label}")
        return 0
    print(f"[FAIL] {label}")
    return 1


def parse_exports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == "__all__"
                for target in node.targets
            ):
                if isinstance(node.value, (ast.List, ast.Tuple)):
                    return {
                        element.value
                        for element in node.value.elts
                        if isinstance(element, ast.Constant)
                        and isinstance(element.value, str)
                    }
    return set()


def main() -> int:
    failures = 0

    failures += check(
        all(path.is_file() for path in REQUIRED_FILES),
        "Required Architecture Intelligence files",
    )

    compile_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "compileall",
            "-q",
            "core/architecture",
            "tests/test_genesis_5a1_architecture_foundation.py",
            "dev/verification/verify_genesis_5a1_architecture_foundation.py",
        ],
        cwd=ROOT,
        check=False,
    )
    failures += check(compile_result.returncode == 0, "Package compilation")

    exports = parse_exports(ROOT / "core" / "architecture" / "__init__.py")
    failures += check(
        REQUIRED_EXPORTS.issubset(exports),
        "Stable public Architecture Intelligence exports",
    )

    contracts_text = (
        ROOT / "core" / "architecture" / "contracts.py"
    ).read_text(encoding="utf-8")
    fingerprints_text = (
        ROOT / "core" / "architecture" / "fingerprints.py"
    ).read_text(encoding="utf-8")

    failures += check(
        "@dataclass(frozen=True, slots=True)" in contracts_text,
        "Immutable slotted architecture contracts",
    )
    failures += check(
        "dataclasses.asdict" not in fingerprints_text,
        "Canonical serializer avoids dataclasses.asdict",
    )
    failures += check(
        "subprocess" not in contracts_text
        and "git " not in contracts_text.lower()
        and "os.system" not in contracts_text,
        "Domain contracts contain no repository side effects",
    )

    test_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "-v",
            "tests.test_genesis_5a1_architecture_foundation",
        ],
        cwd=ROOT,
        check=False,
    )
    failures += check(test_result.returncode == 0, "Genesis V-A1 unit tests")

    smoke_code = """
from core.architecture import (
    ArchitectureSnapshot,
    ModuleDefinition,
    architecture_fingerprint,
)

snapshot = ArchitectureSnapshot(
    snapshot_id="smoke",
    repository_root="/repo",
    branch="feature/test",
    commit="abc123",
    modules=(
        ModuleDefinition(
            path="core/example.py",
            module="core.example",
            line_count=1,
        ),
    ),
)
first = snapshot.fingerprint()
second = snapshot.fingerprint()
assert first == second
assert first == architecture_fingerprint(snapshot)
print(first)
"""
    first_smoke = subprocess.run(
        [sys.executable, "-c", smoke_code],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    second_smoke = subprocess.run(
        [sys.executable, "-c", smoke_code],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    failures += check(
        first_smoke.returncode == 0
        and second_smoke.returncode == 0
        and first_smoke.stdout.strip() == second_smoke.stdout.strip(),
        "Deterministic architecture fingerprint smoke test",
    )

    print()
    print("-" * 72)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 72)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
