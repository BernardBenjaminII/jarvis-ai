#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${PROJECT_ROOT}"

passed=0
failed=0
run_check() {
    local label="$1"; shift
    if "$@"; then
        printf '[PASS] %s\n' "${label}"; passed=$((passed + 1))
    else
        printf '[FAIL] %s\n' "${label}"; failed=$((failed + 1))
    fi
}

printf '%s\n' '========================================================================'
printf '%s\n' 'JARVIS — GENESIS VIII-A0-2'
printf '%s\n' 'GOVERNMENT RELATIONSHIPS'
printf '%s\n' '========================================================================'

run_check "VIII-A0-1 prerequisite"     env PYTHON_BIN="${PYTHON_BIN}" ./dev/verify_genesis_viii_a0_1.sh
run_check "Relationship package compilation"     "${PYTHON_BIN}" -m compileall -q core/government/relationships
run_check "Government relationship tests"     "${PYTHON_BIN}" -m unittest -v tests.test_genesis_viii_a0_2_government_relationships
run_check "Public relationship API" "${PYTHON_BIN}" - <<'PY'
from core.government import OrganizationalGraph, OrganizationalRelationship, RelationshipKind
print("OK")
PY
run_check "Architecture document exists"     test -s docs/architecture/genesis_viii_a0_2_government_relationships.md

printf '%s\n' '------------------------------------------------------------------------'
printf 'Checks passed : %d\n' "${passed}"
printf 'Checks failed : %d\n' "${failed}"
[[ ${failed} -eq 0 ]] && status=EXCELLENT || status=FAILED
printf 'Overall status: %s\n' "${status}"
printf '%s\n' '========================================================================'
[[ ${failed} -eq 0 ]]
