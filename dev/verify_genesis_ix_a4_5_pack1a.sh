#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${ROOT}"
passed=0; failed=0
run_check(){ local label="$1"; shift; if "$@"; then echo "[PASS] ${label}"; passed=$((passed+1)); else echo "[FAIL] ${label}"; failed=$((failed+1)); fi; }
echo "========================================================================"
echo "GENESIS IX-A4.5 PACK 1A"
echo "CANONICAL EVIDENCE QUALIFICATION CONTRACTS"
echo "========================================================================"
run_check "Compilation" "${PYTHON_BIN}" -m py_compile core/retrieval/qualification/__init__.py core/retrieval/qualification/enums.py core/retrieval/qualification/contracts.py tests/test_genesis_ix_a4_5_pack1a_runtime_interface.py
run_check "Contract tests" "${PYTHON_BIN}" -m unittest -v tests.test_genesis_ix_a4_5_pack1a_runtime_interface
run_check "Runtime interface certification" env PYTHON_BIN="${PYTHON_BIN}" ./dev/certify_genesis_ix_a4_5_pack1a.sh
run_check "Architecture document" test -s docs/architecture/genesis_ix_a4_5_pack1a_runtime_interface.md
echo "------------------------------------------------------------------------"
echo "Checks passed : ${passed}"
echo "Checks failed : ${failed}"
[[ ${failed} -eq 0 ]] && echo "Overall Status : EXCELLENT" || echo "Overall Status : FAILED"
echo "========================================================================"
[[ ${failed} -eq 0 ]]
