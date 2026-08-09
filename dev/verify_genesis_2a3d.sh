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

printf '%s\n' '======================================================================'
printf '%s\n' 'JARVIS GENESIS II-A3D — LEGACY LABEL COMPATIBILITY'
printf '%s\n' '======================================================================'

run_check "Genesis II-A3D package compilation"     "${PYTHON_BIN}" -m py_compile     dev/verification/genesis_manifest.py     tests/test_genesis_2a3c_hierarchical_manifest_parser.py     tests/test_genesis_2a3d_legacy_label_compatibility.py

run_check "Legacy label compatibility tests"     "${PYTHON_BIN}" -m unittest -v     tests.test_genesis_2a3d_legacy_label_compatibility

run_check "Genesis II-A3B regression"     env PYTHON_BIN="${PYTHON_BIN}" ./dev/verify_genesis_2a3b.sh

run_check "Genesis II-A3C regression"     env PYTHON_BIN="${PYTHON_BIN}" ./dev/verify_genesis_2a3c.sh

run_check "Current Genesis manifest validates"     "${PYTHON_BIN}" dev/verification/genesis_manifest.py --check

printf '%s\n' '----------------------------------------------------------------------'
printf 'Checks passed : %d\n' "${passed}"
printf 'Checks failed : %d\n' "${failed}"
if [[ ${failed} -eq 0 ]]; then
    printf '%s\n' 'Overall status: EXCELLENT'
else
    printf '%s\n' 'Overall status: FAILED'
fi
printf '%s\n' '======================================================================'

[[ ${failed} -eq 0 ]]
