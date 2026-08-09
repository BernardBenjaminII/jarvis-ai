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
printf '%s\n' 'JARVIS — GENESIS VII-B0'
printf '%s\n' 'SYSTEM INTEGRATION AND OBSERVABILITY AUDIT'
printf '%s\n' '========================================================================'

run_check "VII-B0 package compilation"     "${PYTHON_BIN}" -m py_compile     core/executive/integration_audit/models.py     core/executive/integration_audit/auditor.py     dev/tools/run_genesis_vii_b0_integration_audit.py     tests/test_genesis_vii_b0_integration_audit.py

run_check "VII-B0 unit tests"     "${PYTHON_BIN}" -m unittest -v tests.test_genesis_vii_b0_integration_audit

run_check "Read-only integration audit executes"     "${PYTHON_BIN}" dev/tools/run_genesis_vii_b0_integration_audit.py

run_check "Audit report generated"     test -s artifacts/audit/genesis_vii_b0_integration_audit.json

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
