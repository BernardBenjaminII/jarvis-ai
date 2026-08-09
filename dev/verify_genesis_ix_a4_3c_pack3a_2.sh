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
        passed=$((passed+1))
    else
        echo "[FAIL] ${label}"
        failed=$((failed+1))
    fi
}

echo "========================================================================"
echo "GENESIS IX-A4.3C PACK 3A.2"
echo "AST RECONSTRUCTION REPAIR"
echo "========================================================================"

run_check "Compilation" "${PYTHON_BIN}" -m py_compile   core/runtime/source_analysis.py   dev/certification/repair_genesis_ix_a4_3c_ast.py   tests/test_genesis_ix_a4_3c_pack3a_2_ast_repair.py

run_check "AST regression tests" "${PYTHON_BIN}" -m unittest -v   tests.test_genesis_ix_a4_3c_pack3a_2_ast_repair

run_check "Apply repair" "${PYTHON_BIN}" -m   dev.certification.repair_genesis_ix_a4_3c_ast

run_check "Repaired IX-A4.3C compilation" "${PYTHON_BIN}" -m py_compile   core/retrieval/call_graph/reconstructor.py

run_check "IX-A4.3C runtime reconstruction" env PYTHON_BIN="${PYTHON_BIN}"   ./dev/certify_genesis_ix_a4_3c.sh

for report in   runtime_call_graph.json   runtime_call_graph.md   runtime_callable_surface.md   executive_director_inspection.md   orchestrator_flow.json   ix_a4_3b_hook_repair_contract.md   reconstruction_summary.md
do
  run_check "Report ${report}" test -s     "docs/audits/genesis_ix_a4_3c/${report}"
done

run_check "IX-A4.3C verifier" env PYTHON_BIN="${PYTHON_BIN}"   ./dev/verify_genesis_ix_a4_3c.sh

run_check "Architecture document" test -s   docs/architecture/genesis_ix_a4_3c_pack3a_2_ast_reconstruction_repair.md

echo "------------------------------------------------------------------------"
echo "Checks passed : ${passed}"
echo "Checks failed : ${failed}"
[[ ${failed} -eq 0 ]] && echo "Overall Status : EXCELLENT" || echo "Overall Status : FAILED"
echo "========================================================================"
[[ ${failed} -eq 0 ]]
