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
printf '%s\n' 'GENESIS IX-A4.4'
printf '%s\n' 'RUNTIME RETRIEVAL INTEGRATION REPAIR'
printf '%s\n' '========================================================================'

run_check "Compilation" \
    "${PYTHON_BIN}" -m py_compile \
        core/executive/director_dispatch.py \
        dev/certification/repair_genesis_ix_a4_4_runtime_integration.py \
        tests/test_genesis_ix_a4_4_runtime_integration.py

run_check "Unit tests" \
    "${PYTHON_BIN}" -m unittest -v \
        tests.test_genesis_ix_a4_4_runtime_integration

run_check "Apply runtime integration repair" \
    "${PYTHON_BIN}" -m \
        dev.certification.repair_genesis_ix_a4_4_runtime_integration

run_check "Repaired gap tracer compilation" \
    "${PYTHON_BIN}" -m py_compile \
        core/retrieval/gap_trace/tracer.py

run_check "Knowledge gap propagation trace" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/certify_genesis_ix_a4_3b.sh

run_check "IX-A4.3B verifier" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/verify_genesis_ix_a4_3b.sh

run_check "End-to-end retrieval certification" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/certify_genesis_ix_a4_3.sh

for report in \
    runtime_integration_repair.json \
    runtime_integration_repair.md
do
    run_check "IX-A4.4 report ${report}" \
        test -s "docs/audits/genesis_ix_a4_4/${report}"
done

run_check "Architecture document" \
    test -s \
        docs/architecture/genesis_ix_a4_4_runtime_retrieval_integration_repair.md

printf '%s\n' '------------------------------------------------------------------------'
printf 'Checks passed : %d\n' "${passed}"
printf 'Checks failed : %d\n' "${failed}"

if [[ ${failed} -eq 0 ]]; then
    printf '%s\n' 'Overall Status : EXCELLENT'
else
    printf '%s\n' 'Overall Status : FAILED'
fi

printf '%s\n' '========================================================================'
[[ ${failed} -eq 0 ]]
