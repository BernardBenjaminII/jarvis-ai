#!/usr/bin/env python3
"""Certification for Genesis VI-A6.1 persistence contracts."""

from __future__ import annotations

import ast
import hashlib
import importlib
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

REQUIRED_FILES = (
    "core/executive/__init__.py",
    "core/executive/persistence/__init__.py",
    "core/executive/persistence/contracts.py",
    "tests/test_genesis_vi_a61_persistence_contracts.py",
    "docs/architecture/cognition/genesis_vi_a61_persistence_contracts.md",
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
    "sqlite3",
)

EXPECTED_PUBLIC_SYMBOLS = (
    "CheckpointDescriptor",
    "CheckpointReason",
    "IntegrityMetadata",
    "MigrationPath",
    "PersistenceEnvelope",
    "PersistenceIntegrityStatus",
    "PersistenceRecordKind",
    "RecoveryRequest",
    "SchemaIdentity",
)

EXPECTED_FINGERPRINT = "2106cc0af5e29d80dfca5ddd4b84ab7b1958748e2f71dc8f192fdd2c2a9670d8"


def check_required_files() -> Tuple[bool, str]:
    missing = [
        path
        for path in REQUIRED_FILES
        if not (PROJECT_ROOT / path).is_file()
    ]
    if missing:
        return False, f"Missing required files: {missing}"
    return True, "Canonical Genesis VI-A6.1 file structure"


def check_compilation() -> Tuple[bool, str]:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "compileall",
            "-q",
            str(PROJECT_ROOT / "core" / "executive"),
            str(
                PROJECT_ROOT
                / "tests"
                / "test_genesis_vi_a61_persistence_contracts.py"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return False, result.stderr.strip() or result.stdout.strip()
    return True, "Genesis VI-A6.1 package compilation"


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
    package = PROJECT_ROOT / "core" / "executive" / "persistence"
    for path in sorted(package.glob("*.py")):
        for module in imported_modules(path):
            if module.startswith(FORBIDDEN_IMPORT_PREFIXES):
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)} -> {module}"
                )
    if violations:
        return False, f"Forbidden persistence dependencies: {violations}"
    return True, "Vendor, model, network, and storage isolation"


def check_public_imports() -> Tuple[bool, str]:
    module = importlib.import_module("core.executive.persistence")
    missing = [
        symbol
        for symbol in EXPECTED_PUBLIC_SYMBOLS
        if not hasattr(module, symbol)
    ]
    missing.extend(
        symbol
        for symbol in module.__all__
        if not hasattr(module, symbol)
    )
    if missing:
        return False, f"Missing public symbols: {sorted(set(missing))}"
    return True, "Stable Genesis VI-A6.1 public imports"


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
            item
            for item in (
                result.stdout.strip(),
                result.stderr.strip(),
            )
            if item
        )
        return False, output
    return True, label


def check_a61_tests() -> Tuple[bool, str]:
    return run_unittest(
        "tests.test_genesis_vi_a61_persistence_contracts",
        "Genesis VI-A6.1 persistence-contract unit tests",
    )


def check_a5_regression() -> Tuple[bool, str]:
    return run_unittest(
        "tests.test_genesis_vi_a5_executive_session",
        "Genesis VI-A5 regression",
    )


def check_a4_regression() -> Tuple[bool, str]:
    return run_unittest(
        "tests.test_genesis_vi_a4_cognition_cycle_controller",
        "Genesis VI-A4 regression",
    )


def check_a3_regression() -> Tuple[bool, str]:
    return run_unittest(
        "tests.test_genesis_vi_a3_cognitive_state_machine",
        "Genesis VI-A3 regression",
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


def deterministic_contract_fingerprint() -> str:
    from core.executive.persistence import (
        CheckpointDescriptor,
        CheckpointReason,
        IntegrityMetadata,
        MigrationPath,
        PersistenceEnvelope,
        PersistenceIntegrityStatus,
        PersistenceRecordKind,
        RecoveryRequest,
        SchemaIdentity,
    )

    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    schema = SchemaIdentity()
    integrity = IntegrityMetadata(
        algorithm="sha256",
        digest="b" * 64,
        status=PersistenceIntegrityStatus.VERIFIED,
    )
    envelope = PersistenceEnvelope(
        record_id="record-001",
        record_kind=PersistenceRecordKind.SESSION_SNAPSHOT,
        schema=schema,
        session_id="session-001",
        mission_id="mission-001",
        executive_id="victor",
        created_at=now,
        payload_size=4096,
        integrity=integrity,
        metadata={"phase": "vi-a6.1", "certified": "true"},
    )
    checkpoint = CheckpointDescriptor(
        checkpoint_id="checkpoint-001",
        session_id="session-001",
        sequence=1,
        reason=CheckpointReason.MANUAL,
        record_id=envelope.record_id,
        created_at=now,
        tags=("certification", "foundation"),
    )
    migration = MigrationPath(
        schema_name=schema.name,
        source_version=1,
        target_version=2,
        migration_id="migration-1-to-2",
    )
    recovery = RecoveryRequest(
        session_id="session-001",
        checkpoint_id=checkpoint.checkpoint_id,
    )

    payload = "|".join(
        (
            schema.canonical,
            integrity.algorithm,
            integrity.digest,
            integrity.status.value,
            envelope.record_id,
            envelope.record_kind.value,
            envelope.session_id,
            envelope.mission_id,
            envelope.executive_id,
            str(envelope.payload_size),
            ",".join(envelope.metadata),
            checkpoint.checkpoint_id,
            str(checkpoint.sequence),
            checkpoint.reason.value,
            ",".join(checkpoint.tags),
            migration.source.canonical,
            migration.target.canonical,
            migration.migration_id,
            recovery.session_id,
            str(recovery.require_verified_integrity),
            str(recovery.allow_migration),
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def check_deterministic_fingerprint() -> Tuple[bool, str]:
    actual = deterministic_contract_fingerprint()
    if actual != EXPECTED_FINGERPRINT:
        return (
            False,
            "Deterministic contract fingerprint mismatch: "
            f"expected {EXPECTED_FINGERPRINT}, got {actual}",
        )
    return True, "Deterministic persistence-contract fingerprint"


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
    print("JARVIS — GENESIS VI-A6.1 PERSISTENCE CONTRACTS")
    print("=" * 72)

    checks = (
        check_required_files,
        check_compilation,
        check_dependency_isolation,
        check_public_imports,
        check_a61_tests,
        check_a5_regression,
        check_a4_regression,
        check_a3_regression,
        check_a2_regression,
        check_a1_regression,
        check_deterministic_fingerprint,
    )

    failures = 0
    for check in checks:
        passed, detail = run_check(check)
        print(f"[{'PASS' if passed else 'FAIL'}] {detail}")
        if not passed:
            failures += 1

    print("-" * 72)
    print(f"Checks failed : {failures}")
    print(
        "Overall status: "
        + ("EXCELLENT" if failures == 0 else "FAILED")
    )
    print("=" * 72)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
