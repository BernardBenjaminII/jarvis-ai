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
printf '%s\n' 'JARVIS — GENESIS VIII-A0-3'
printf '%s\n' 'CANONICAL GOVERNMENT SERIALIZATION'
printf '%s\n' '========================================================================'

run_check "VIII-A0-2 prerequisite" \
    env PYTHON_BIN="${PYTHON_BIN}" ./dev/verify_genesis_viii_a0_2.sh

run_check "Serialization package compilation" \
    "${PYTHON_BIN}" -m compileall -q core/government/serialization

run_check "Canonical serialization tests" \
    "${PYTHON_BIN}" -m unittest -v \
        tests.test_genesis_viii_a0_3_canonical_government_serialization

run_check "Public serialization API" \
    "${PYTHON_BIN}" - <<'PY'
from core.government import (
    GOVERNMENT_SCHEMA_VERSION,
    GovernmentCodec,
    GovernmentEnvelope,
)
assert GOVERNMENT_SCHEMA_VERSION == "1.0.0"
print("OK")
PY

run_check "Architecture document exists" \
    test -s docs/architecture/genesis_viii_a0_3_canonical_government_serialization.md

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
