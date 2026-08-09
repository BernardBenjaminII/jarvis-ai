#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${ROOT}"

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
printf '%s\n' 'JARVIS — GENESIS IX-A4.1B PACK 1'
printf '%s\n' 'RETRIEVAL AUDIT ENGINE'
printf '%s\n' '========================================================================'

run_check "Pack 1 compilation" \
    "${PYTHON_BIN}" -m py_compile \
        dev/audits/audit_genesis_ix_a4_1b_pack1_retrieval_runtime.py \
        tests/test_genesis_ix_a4_1b_pack1_retrieval_runtime.py

run_check "Pack 1 tests" \
    "${PYTHON_BIN}" -m unittest -v \
        tests.test_genesis_ix_a4_1b_pack1_retrieval_runtime

run_check "Live retrieval inventory" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/audit_genesis_ix_a4_1b_pack1.sh

run_check "Runtime JSON report" \
    test -s docs/audits/genesis_ix_a4_1b_pack1/retrieval_runtime_inventory.json

run_check "Runtime Markdown report" \
    test -s docs/audits/genesis_ix_a4_1b_pack1/retrieval_runtime_inventory.md

run_check "IX-A4.1A regression" \
    env PYTHON_BIN="${PYTHON_BIN}" ./dev/verify_genesis_ix_a4_1a.sh

run_check "Architecture charter" \
    test -s docs/architecture/genesis_ix_a4_1b_pack1_retrieval_audit_engine.md

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
