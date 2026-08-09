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
printf '%s\n' 'JARVIS — GENESIS VIII-B0'
printf '%s\n' 'ORGANIZATIONAL REGISTRY'
printf '%s\n' '========================================================================'

run_check "VIII-A0 Government Framework prerequisite" \
    env PYTHON_BIN="${PYTHON_BIN}" ./dev/verify_genesis_viii_a0_6.sh

run_check "Organizational Registry package compilation" \
    "${PYTHON_BIN}" -m compileall -q core/government/registry

run_check "Organizational Registry tests" \
    "${PYTHON_BIN}" -m unittest -v \
        tests.test_genesis_viii_b0_organizational_registry

run_check "Canonical Government bootstrap" \
    "${PYTHON_BIN}" - <<'PY'
from core.government import bootstrap_government

result = bootstrap_government()
assert result.object_count >= 15
assert result.relationship_count >= 14
print(result.fingerprint)
PY

run_check "Public Organizational Registry API" \
    "${PYTHON_BIN}" - <<'PY'
from core.government import (
    InMemoryGovernmentRegistry,
    InMemoryRegistryProvider,
    bootstrap_government,
)
print("OK")
PY

run_check "No persistence dependency introduced" \
    "${PYTHON_BIN}" - <<'PY'
from pathlib import Path

for path in (
    Path("core/government/registry/memory.py"),
    Path("core/government/registry/bootstrap.py"),
    Path("core/government/registry/provider_memory.py"),
):
    source = path.read_text(encoding="utf-8")
    for token in ("sqlite3", "sqlalchemy", "psycopg", "lmdb", "open(", "Path("):
        assert token not in source, f"{path}: forbidden dependency {token}"
print("OK")
PY

run_check "Architecture document exists" \
    test -s docs/architecture/genesis_viii_b0_organizational_registry.md

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
