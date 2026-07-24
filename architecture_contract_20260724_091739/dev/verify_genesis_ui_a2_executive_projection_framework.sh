#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
cd "$ROOT"
echo "========================================================================"
echo "JARVIS — GENESIS UI-A2 EXECUTIVE PROJECTION FRAMEWORK"
echo "========================================================================"
failures=0
run_check(){ local label="$1"; shift; if "$@"; then echo "[PASS] $label"; else echo "[FAIL] $label"; failures=$((failures+1)); fi; }
run_check "Structural verification" "$PYTHON_BIN" dev/verification/verify_genesis_ui_a2_executive_projection_framework.py
run_check "Python compilation" "$PYTHON_BIN" -m py_compile core/integration/*.py core/integration/providers/*.py core/src/routes/operations.py tests/test_genesis_ui_a2_executive_projection_framework.py
run_check "UI-A2 unit tests" "$PYTHON_BIN" -m unittest tests.test_genesis_ui_a2_executive_projection_framework
run_check "Integration import smoke test" "$PYTHON_BIN" -c "from core.integration import get_default_integration_runtime; r=get_default_integration_runtime(); assert 'operations' in r.projection_registry; assert 'capabilities' in r.projection_registry"
if [[ -x ./dev/verify_executive_integration_pack.sh ]]; then run_check "UI-A1 regression" env PYTHON_BIN="$PYTHON_BIN" ./dev/verify_executive_integration_pack.sh; fi
echo "------------------------------------------------------------------------"
echo "Checks failed : $failures"
if [[ "$failures" -eq 0 ]]; then echo "Overall status: EXCELLENT"; echo "========================================================================"; exit 0; fi
echo "Overall status: FAILED"; echo "========================================================================"; exit 1
