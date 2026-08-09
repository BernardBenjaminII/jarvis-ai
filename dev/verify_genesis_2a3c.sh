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
printf '%s\n' 'JARVIS GENESIS II-A3C — HIERARCHICAL MANIFEST PARSER'
printf '%s\n' '======================================================================'

run_check "Genesis II-A3C package compilation" \
    "${PYTHON_BIN}" -m py_compile \
    dev/verification/genesis_manifest.py \
    tests/test_genesis_2a3c_hierarchical_manifest_parser.py

run_check "Hierarchical parser unit tests" \
    "${PYTHON_BIN}" -m unittest -v \
    tests.test_genesis_2a3c_hierarchical_manifest_parser

run_check "Current Genesis manifest validates" \
    "${PYTHON_BIN}" dev/verification/genesis_manifest.py --check

run_check "Genesis II-A3B regression" \
    env PYTHON_BIN="${PYTHON_BIN}" ./dev/verify_genesis_2a3b.sh

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
