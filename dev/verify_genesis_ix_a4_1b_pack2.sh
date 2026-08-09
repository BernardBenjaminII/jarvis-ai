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
printf '%s\n' 'JARVIS — GENESIS IX-A4.1B PACK 2'
printf '%s\n' 'RETRIEVAL REPORTS & CANONICALIZATION'
printf '%s\n' '========================================================================'

run_check "Pack 2 compilation" \
    "${PYTHON_BIN}" -m py_compile \
        dev/audits/generate_genesis_ix_a4_1b_pack2_reports.py \
        tests/test_genesis_ix_a4_1b_pack2_reports.py

run_check "Pack 2 tests" \
    "${PYTHON_BIN}" -m unittest -v \
        tests.test_genesis_ix_a4_1b_pack2_reports

run_check "Pack 1 inventory exists" \
    test -s docs/audits/genesis_ix_a4_1b_pack1/retrieval_runtime_inventory.json

run_check "Generate Pack 2 reports" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/generate_genesis_ix_a4_1b_pack2_reports.sh

for report in \
    retrieval_runtime_graph.md \
    retrieval_component_matrix.md \
    retrieval_duplicate_report.md \
    retrieval_embedding_coverage.md \
    retrieval_table_ownership.md \
    retrieval_canonicalization_report.md \
    retrieval_report_manifest.json
do
    run_check "Report ${report}" \
        test -s "docs/audits/genesis_ix_a4_1b_pack2/${report}"
done

run_check "Pack 1 regression" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/verify_genesis_ix_a4_1b_pack1.sh

run_check "Architecture charter" \
    test -s docs/architecture/genesis_ix_a4_1b_pack2_retrieval_reports.md

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
