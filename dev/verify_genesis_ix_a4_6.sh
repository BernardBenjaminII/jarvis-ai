#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${ROOT}"
passed=0; failed=0
run_check(){ local label="$1"; shift; if "$@"; then echo "[PASS] ${label}"; passed=$((passed+1)); else echo "[FAIL] ${label}"; failed=$((failed+1)); fi; }
echo "========================================================================"
echo "GENESIS IX-A4.6"
echo "GROUNDED ANSWER ENGINE"
echo "========================================================================"
run_check "Compilation" "${PYTHON_BIN}" -m py_compile core/retrieval/grounded_answer/*.py tests/test_genesis_ix_a4_6_grounded_answer_engine.py
run_check "Grounded answer tests" "${PYTHON_BIN}" -m unittest -v tests.test_genesis_ix_a4_6_grounded_answer_engine
run_check "Grounded answer certification" env PYTHON_BIN="${PYTHON_BIN}" ./dev/certify_genesis_ix_a4_6.sh
run_check "IX-A4.5 regression" env PYTHON_BIN="${PYTHON_BIN}" ./dev/verify_genesis_ix_a4_5_pack3a_2.sh
run_check "Architecture document" test -s docs/architecture/genesis_ix_a4_6_grounded_answer_engine.md
echo "------------------------------------------------------------------------"
echo "Checks passed : ${passed}"
echo "Checks failed : ${failed}"
[[ ${failed} -eq 0 ]] && echo "Overall Status : EXCELLENT" || echo "Overall Status : FAILED"
echo "========================================================================"
[[ ${failed} -eq 0 ]]
