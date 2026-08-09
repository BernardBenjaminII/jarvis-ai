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
printf '%s\n' 'JARVIS — GENESIS VIII-A0-1'
printf '%s\n' 'CONSTITUTIONAL OBJECT MODEL'
printf '%s\n' '========================================================================'

run_check "Package compilation" "${PYTHON_BIN}" -m compileall -q core/government
run_check "Constitutional object model tests" \
    "${PYTHON_BIN}" -m unittest -v tests.test_genesis_viii_a0_1_constitutional_object_model
run_check "Public API import" "${PYTHON_BIN}" - <<'PY'
from core.government.models import Government, ExecutiveOffice, Directorate, Department
print("OK")
PY
run_check "GOA-0000 constitutional source present" \
    test -s docs/constitution/GOA-0000_ORGANIZATIONAL_CONSTITUTION.md

printf '%s\n' '------------------------------------------------------------------------'
printf 'Checks passed : %d\n' "${passed}"
printf 'Checks failed : %d\n' "${failed}"
[[ ${failed} -eq 0 ]] && status=EXCELLENT || status=FAILED
printf 'Overall status: %s\n' "${status}"
printf '%s\n' '========================================================================'
[[ ${failed} -eq 0 ]]
