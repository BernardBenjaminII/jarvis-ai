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
        echo "[PASS] ${label}"
        passed=$((passed + 1))
    else
        echo "[FAIL] ${label}"
        failed=$((failed + 1))
    fi
}

echo "========================================================================"
echo "GENESIS IX-A4.7 PACK 2B"
echo "EXECUTIVE ORCHESTRATOR INTEGRATION"
echo "========================================================================"

run_check "Compilation" \
    "${PYTHON_BIN}" -m py_compile \
        core/conversation/grounded_answer/integration.py \
        dev/certification/repair_genesis_ix_a4_7_pack2b.py \
        tests/test_genesis_ix_a4_7_pack2b_orchestrator_integration.py

run_check "Integration tests" \
    "${PYTHON_BIN}" -m unittest -v \
        tests.test_genesis_ix_a4_7_pack2b_orchestrator_integration

run_check "Apply orchestrator integration" \
    "${PYTHON_BIN}" -m \
        dev.certification.repair_genesis_ix_a4_7_pack2b

run_check "Production compilation" \
    "${PYTHON_BIN}" -m py_compile \
        core/conversation/orchestrator.py

run_check "Live orchestrator certification" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/certify_genesis_ix_a4_7_pack2b.sh

run_check "Pack 2A regression" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/verify_genesis_ix_a4_7_pack2a.sh

run_check "Pack 1 regression" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/verify_genesis_ix_a4_7_pack1.sh

run_check "IX-A4.3 end-to-end retrieval" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/certify_genesis_ix_a4_3.sh

run_check "Architecture document" \
    test -s \
        docs/architecture/genesis_ix_a4_7_pack2b_orchestrator_integration.md

for report in orchestrator_integration.json orchestrator_integration.md
do
    run_check "Report ${report}" \
        test -s "docs/audits/genesis_ix_a4_7_pack2b/${report}"
done

echo "------------------------------------------------------------------------"
echo "Checks passed : ${passed}"
echo "Checks failed : ${failed}"

if [[ ${failed} -eq 0 ]]; then
    echo "Overall Status : EXCELLENT"
else
    echo "Overall Status : FAILED"
fi

echo "========================================================================"
[[ ${failed} -eq 0 ]]
