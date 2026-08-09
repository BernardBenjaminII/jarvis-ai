#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${ROOT}"
passed=0
failed=0
run_check(){ local label="$1"; shift; if "$@"; then echo "[PASS] ${label}"; passed=$((passed+1)); else echo "[FAIL] ${label}"; failed=$((failed+1)); fi; }

echo "========================================================================"
echo "GENESIS IX-A4.8 PACK 2"
echo "EXECUTIVE ACCEPTANCE HARNESS"
echo "========================================================================"

run_check "Compilation" "${PYTHON_BIN}" -m py_compile   dev/acceptance/*.py dev/run_genesis_ix_a4_8_acceptance.py   dev/certify_genesis_ix_a4_8_pack2.py   tests/test_genesis_ix_a4_8_pack2_acceptance_harness.py

run_check "Harness tests" "${PYTHON_BIN}" -m unittest -v   tests.test_genesis_ix_a4_8_pack2_acceptance_harness

run_check "Harness certification" "${PYTHON_BIN}"   dev/certify_genesis_ix_a4_8_pack2.py

run_check "Pack 1 regression" env PYTHON_BIN="${PYTHON_BIN}"   ./dev/verify_genesis_ix_a4_8_pack1.sh

run_check "Architecture document" test -s   docs/architecture/genesis_ix_a4_8_pack2_acceptance_harness.md

echo "------------------------------------------------------------------------"
echo "Checks passed : ${passed}"
echo "Checks failed : ${failed}"
[[ ${failed} -eq 0 ]] && echo "Overall Status : EXCELLENT" || echo "Overall Status : FAILED"
echo "========================================================================"
[[ ${failed} -eq 0 ]]
