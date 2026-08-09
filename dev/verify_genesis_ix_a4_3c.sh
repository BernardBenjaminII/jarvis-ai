#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; PYTHON_BIN="${PYTHON_BIN:-python}"; cd "${ROOT}"; passed=0; failed=0
run(){ local l="$1"; shift; if "$@"; then echo "[PASS] $l"; passed=$((passed+1)); else echo "[FAIL] $l"; failed=$((failed+1)); fi; }
echo "========================================================================"; echo "GENESIS IX-A4.3C"; echo "EXECUTIVE RUNTIME CALL GRAPH RECONSTRUCTION"; echo "========================================================================"
run "Compilation" "${PYTHON_BIN}" -m py_compile core/retrieval/call_graph/reconstructor.py dev/certification/certify_genesis_ix_a4_3c.py tests/test_genesis_ix_a4_3c_call_graph_reconstruction.py
run "Unit tests" "${PYTHON_BIN}" -m unittest -v tests.test_genesis_ix_a4_3c_call_graph_reconstruction
run "Runtime call graph reconstruction" env PYTHON_BIN="${PYTHON_BIN}" ./dev/certify_genesis_ix_a4_3c.sh
for f in runtime_call_graph.json runtime_call_graph.md runtime_callable_surface.md executive_director_inspection.md orchestrator_flow.json ix_a4_3b_hook_repair_contract.md reconstruction_summary.md; do run "Report $f" test -s "docs/audits/genesis_ix_a4_3c/$f"; done
run "IX-A4.3A regression" env PYTHON_BIN="${PYTHON_BIN}" ./dev/verify_genesis_ix_a4_3a.sh
run "IX-A4.2A regression" env PYTHON_BIN="${PYTHON_BIN}" ./dev/verify_genesis_ix_a4_2a.sh
run "Architecture document" test -s docs/architecture/genesis_ix_a4_3c_executive_runtime_call_graph_reconstruction.md
echo "------------------------------------------------------------------------"; echo "Checks passed : $passed"; echo "Checks failed : $failed"; [[ $failed -eq 0 ]] && echo "Overall Status : EXCELLENT" || echo "Overall Status : FAILED"; echo "========================================================================"; [[ $failed -eq 0 ]]
