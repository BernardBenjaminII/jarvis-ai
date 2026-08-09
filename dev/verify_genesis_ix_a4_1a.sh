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
echo "JARVIS — GENESIS IX-A4.1A"
echo "EXECUTIVE & CONVERSATION INVENTORY"
echo "========================================================================"
run_check "IX-A4.1A compilation"   "${PYTHON_BIN}" -m py_compile   dev/audits/audit_genesis_ix_a4_1a_executive_conversation_inventory.py   tests/test_genesis_ix_a4_1a_executive_conversation_inventory.py
run_check "IX-A4.1A tests"   "${PYTHON_BIN}" -m unittest -v   tests.test_genesis_ix_a4_1a_executive_conversation_inventory
run_check "Live inventory"   env PYTHON_BIN="${PYTHON_BIN}" ./dev/audit_genesis_ix_a4_1a.sh
for report in   executive_inventory.md   conversation_inventory.md   executive_dependency_graph.md   executive_runtime_inventory.json   executive_call_graph.md   executive_component_matrix.md   executive_duplicate_report.md
do
  run_check "Report ${report}"     test -s "docs/audits/genesis_ix_a4_1a/${report}"
done
run_check "IX-A4 regression"   env PYTHON_BIN="${PYTHON_BIN}" ./dev/verify_genesis_ix_a4.sh
run_check "Architecture charter"   test -s docs/architecture/genesis_ix_a4_1a_executive_conversation_inventory.md
echo "------------------------------------------------------------------------"
echo "Checks passed : ${passed}"
echo "Checks failed : ${failed}"
[[ ${failed} -eq 0 ]] && echo "Overall status: EXCELLENT" || echo "Overall status: FAILED"
echo "========================================================================"
[[ ${failed} -eq 0 ]]
