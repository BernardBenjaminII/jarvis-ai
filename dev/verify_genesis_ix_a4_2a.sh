#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${ROOT}"
passed=0
failed=0
run_check() {
    local label="$1"; shift
    if "$@"; then echo "[PASS] ${label}"; passed=$((passed+1))
    else echo "[FAIL] ${label}"; failed=$((failed+1)); fi
}
echo "========================================================================"
echo "GENESIS IX-A4.2A"
echo "RETRIEVAL PIPELINE INVENTORY"
echo "========================================================================"
run_check "Compilation" "${PYTHON_BIN}" -m py_compile     core/retrieval/inspection.py core/retrieval/inventory.py     dev/certification/certify_genesis_ix_a4_2a_inventory.py     tests/test_genesis_ix_a4_2a_inventory.py
run_check "Unit tests" "${PYTHON_BIN}" -m unittest -v tests.test_genesis_ix_a4_2a_inventory
run_check "Retrieval inventory" env PYTHON_BIN="${PYTHON_BIN}" ./dev/certify_genesis_ix_a4_2a.sh
for report in pipeline_inventory.json retrieval_graph.json runtime_inventory.md capability_matrix.md retrieval_graph.md
do
    run_check "Report ${report}" test -s "docs/audits/retrieval_inventory/${report}"
done
run_check "Pack 3A.1 regression" env PYTHON_BIN="${PYTHON_BIN}" ./dev/verify_genesis_ix_a4_1b_pack3a_1.sh
run_check "Architecture document" test -s docs/architecture/genesis_ix_a4_2a_retrieval_pipeline_inventory.md
echo "------------------------------------------------------------------------"
echo "Checks passed : ${passed}"
echo "Checks failed : ${failed}"
[[ ${failed} -eq 0 ]] && echo "Overall Status : EXCELLENT" || echo "Overall Status : FAILED"
echo "========================================================================"
[[ ${failed} -eq 0 ]]
