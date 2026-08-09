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
printf '%s\n' 'GENESIS IX-A4.3'
printf '%s\n' 'END-TO-END RETRIEVAL CERTIFICATION'
printf '%s\n' '========================================================================'

run_check "Compilation" \
    "${PYTHON_BIN}" -m py_compile \
        core/retrieval/certification/contracts.py \
        core/retrieval/certification/tracer.py \
        dev/certification/certify_genesis_ix_a4_3.py \
        tests/test_genesis_ix_a4_3_end_to_end_retrieval.py

run_check "Unit tests" \
    "${PYTHON_BIN}" -m unittest -v \
        tests.test_genesis_ix_a4_3_end_to_end_retrieval

run_check "End-to-end retrieval certification" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/certify_genesis_ix_a4_3.sh

for report in \
    end_to_end_certification.json \
    end_to_end_certification.md \
    known_retrieval_trace.md \
    gap_retrieval_trace.md \
    stage_matrix.md \
    grounded_prompt_contract.md
do
    run_check "Report ${report}" \
        test -s "docs/audits/genesis_ix_a4_3/${report}"
done

run_check "IX-A4.2A regression" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/verify_genesis_ix_a4_2a.sh

run_check "Architecture document" \
    test -s \
        docs/architecture/genesis_ix_a4_3_end_to_end_retrieval_certification.md

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
