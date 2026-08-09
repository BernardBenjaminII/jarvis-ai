#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${ROOT}"
passed=0
failed=0
run_check(){ local label="$1"; shift; if "$@"; then echo "[PASS] ${label}"; passed=$((passed+1)); else echo "[FAIL] ${label}"; failed=$((failed+1)); fi; }

echo "========================================================================"
echo "GENESIS IX-A4.5 PACK 3A"
echo "RUNTIME INTEGRATION"
echo "========================================================================"

run_check "Compilation" "${PYTHON_BIN}" -m py_compile   core/knowledge_catalog/qualified_search.py   dev/certification/repair_genesis_ix_a4_5_pack3a.py   tests/test_genesis_ix_a4_5_pack3a_runtime_integration.py

run_check "Integration adapter tests" "${PYTHON_BIN}" -m unittest -v   tests.test_genesis_ix_a4_5_pack3a_runtime_integration

run_check "Runtime integration certification" env PYTHON_BIN="${PYTHON_BIN}"   ./dev/certify_genesis_ix_a4_5_pack3a.sh

run_check "Pack 2A regression" env PYTHON_BIN="${PYTHON_BIN}"   ./dev/verify_genesis_ix_a4_5_pack2a.sh

run_check "IX-A4.3 end-to-end recertification" env PYTHON_BIN="${PYTHON_BIN}"   ./dev/certify_genesis_ix_a4_3.sh

run_check "Architecture document" test -s   docs/architecture/genesis_ix_a4_5_pack3a_runtime_integration.md

for report in runtime_integration.json runtime_integration.md
do
  run_check "Report ${report}" test -s     "docs/audits/genesis_ix_a4_5_pack3a/${report}"
done

echo "------------------------------------------------------------------------"
echo "Checks passed : ${passed}"
echo "Checks failed : ${failed}"
[[ ${failed} -eq 0 ]] && echo "Overall Status : EXCELLENT" || echo "Overall Status : FAILED"
echo "========================================================================"
[[ ${failed} -eq 0 ]]
