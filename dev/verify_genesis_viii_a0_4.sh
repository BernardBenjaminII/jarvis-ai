#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${PROJECT_ROOT}"

passed=0
failed=0

run_check() {
    local label="$1"
    shift
    if "$@"; then
        printf '[PASS] %s\n' "${label}"
        passed=$((passed + 1))
    else
        printf '[FAIL] %s\n' "${label}"
        failed=$((failed + 1))
    fi
}

printf '%s\n' '========================================================================'
printf '%s\n' 'JARVIS — GENESIS VIII-A0-4'
printf '%s\n' 'ORGANIZATIONAL REGISTRY INTERFACES'
printf '%s\n' '========================================================================'

run_check "VIII-A0-3 prerequisite" \
    env PYTHON_BIN="${PYTHON_BIN}" ./dev/verify_genesis_viii_a0_3.sh

run_check "Registry interface package compilation" \
    "${PYTHON_BIN}" -m compileall -q core/government/registry

run_check "Registry interface tests" \
    "${PYTHON_BIN}" -m unittest -v \
        tests.test_genesis_viii_a0_4_organizational_registry_interfaces

run_check "Public registry API" \
    "${PYTHON_BIN}" - <<'PY'
from core.government import (
    GovernmentRegistry,
    ObjectRepository,
    RelationshipRepository,
    GovernmentSnapshotRepository,
    RegistryProvider,
    RegistryTransaction,
    GovernmentSnapshot,
)
print("OK")
PY

run_check "No persistence implementation dependencies" \
    "${PYTHON_BIN}" - <<'PY'
from pathlib import Path

root = Path("core/government/registry")
for path in root.glob("*.py"):
    source = path.read_text(encoding="utf-8")
    forbidden = ("sqlite3", "sqlalchemy", "psycopg", "lmdb", "pathlib.Path(", "open(")
    for token in forbidden:
        assert token not in source, f"{path}: forbidden dependency {token}"
print("OK")
PY

run_check "Architecture document exists" \
    test -s docs/architecture/genesis_viii_a0_4_organizational_registry_interfaces.md

printf '%s\n' '------------------------------------------------------------------------'
printf 'Checks passed : %d\n' "${passed}"
printf 'Checks failed : %d\n' "${failed}"
if [[ ${failed} -eq 0 ]]; then
    printf '%s\n' 'Overall status: EXCELLENT'
else
    printf '%s\n' 'Overall status: FAILED'
fi
printf '%s\n' '========================================================================'

[[ ${failed} -eq 0 ]]
