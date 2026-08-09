#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${ROOT}"
passed=0
failed=0
run_check(){ local label="$1"; shift; if "$@"; then echo "[PASS] ${label}"; passed=$((passed+1)); else echo "[FAIL] ${label}"; failed=$((failed+1)); fi; }

echo "========================================================================"
echo "GENESIS IX-A4.3B"
echo "KNOWLEDGE GAP PROPAGATION TRACE"
echo "========================================================================"

run_check "Compilation" "${PYTHON_BIN}" -m py_compile  core/retrieval/gap_trace/tracer.py  dev/certification/certify_genesis_ix_a4_3b.py  tests/test_genesis_ix_a4_3b_gap_propagation_trace.py

run_check "Unit tests" "${PYTHON_BIN}" -m unittest -v tests.test_genesis_ix_a4_3b_gap_propagation_trace
run_check "Gap propagation trace" env PYTHON_BIN="${PYTHON_BIN}" ./dev/certify_genesis_ix_a4_3b.sh

for report in gap_creation_trace.md gap_propagation_trace.md knowledge_gap_graph.md mutation_trace.md prompt_trace.md decision_tree.md runtime_objects.json trace_summary.json trace_summary.md
do
 run_check "Report ${report}" test -s "docs/audits/genesis_ix_a4_3b/${report}"
done

run_check "IX-A4.3A regression" env PYTHON_BIN="${PYTHON_BIN}" ./dev/verify_genesis_ix_a4_3a.sh
run_check "IX-A4.2A regression" env PYTHON_BIN="${PYTHON_BIN}" ./dev/verify_genesis_ix_a4_2a.sh
run_check "Architecture document" test -s docs/architecture/genesis_ix_a4_3b_knowledge_gap_propagation_trace.md

echo "------------------------------------------------------------------------"
echo "Checks passed : ${passed}"
echo "Checks failed : ${failed}"
[[ ${failed} -eq 0 ]] && echo "Overall Status : EXCELLENT" || echo "Overall Status : FAILED"
echo "========================================================================"
[[ ${failed} -eq 0 ]]
