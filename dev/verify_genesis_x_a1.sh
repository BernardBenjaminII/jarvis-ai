#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "$ROOT"
passed=0; failed=0
check(){ local label="$1"; shift; if "$@"; then echo "[PASS] $label"; passed=$((passed+1)); else echo "[FAIL] $label"; failed=$((failed+1)); fi; }
echo "========================================================================"
echo "GENESIS X-A1 — PRODUCTION MATERIALIZATION ENGINE"
echo "========================================================================"
check "Compilation" "$PYTHON_BIN" -m py_compile core/knowledge_catalog/production_materialization/*.py dev/run_genesis_x_a1.py dev/certify_genesis_x_a1.py tests/test_genesis_x_a1.py
check "Tests" "$PYTHON_BIN" -m unittest -v tests.test_genesis_x_a1
check "Certification" "$PYTHON_BIN" -m dev.certify_genesis_x_a1
check "CLI help" "$PYTHON_BIN" -m dev.run_genesis_x_a1 --help
check "Architecture" test -s docs/architecture/genesis_x_a1_production_materialization_engine.md
check "Runbook" test -s docs/operations/genesis_x_a1_runbook.md
echo "------------------------------------------------------------------------"
echo "Checks passed : $passed"; echo "Checks failed : $failed"
[[ $failed -eq 0 ]] && echo "Overall Status : EXCELLENT" || echo "Overall Status : FAILED"
echo "========================================================================"
[[ $failed -eq 0 ]]
