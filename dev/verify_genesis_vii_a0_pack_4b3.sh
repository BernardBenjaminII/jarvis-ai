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
printf '%s\n' 'JARVIS — GENESIS VII-A0 PACK 4B-3'
printf '%s\n' 'CAPABILITY NAMESPACE CONSOLIDATION'
printf '%s\n' '========================================================================'

run_check "Legacy capability contract migrated" \
    test ! -e core/executive/capabilities.py

run_check "Canonical legacy contract module exists" \
    test -f core/executive/capability_contracts.py

run_check "Package compilation" \
    "${PYTHON_BIN}" -m py_compile \
        core/executive/capability_contracts.py \
        core/executive/capabilities/__init__.py \
        tests/test_genesis_vii_a0_pack_4b3_namespace_consolidation.py

run_check "Namespace consolidation unit tests" \
    "${PYTHON_BIN}" -m unittest -v \
        tests.test_genesis_vii_a0_pack_4b3_namespace_consolidation

run_check "DirectorReadiness public import" \
    "${PYTHON_BIN}" - <<'PY'
from core.executive.capabilities import DirectorReadiness
assert DirectorReadiness.READY.value == "ready"
print("OK")
PY

run_check "ExecutiveDirector public import" \
    "${PYTHON_BIN}" - <<'PY'
from core.executive.director import ExecutiveDirector
assert ExecutiveDirector.__name__ == "ExecutiveDirector"
print("OK")
PY

run_check "FastAPI application import" \
    "${PYTHON_BIN}" - <<'PY'
from core.src.main import app
assert app is not None
print("OK")
PY

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
