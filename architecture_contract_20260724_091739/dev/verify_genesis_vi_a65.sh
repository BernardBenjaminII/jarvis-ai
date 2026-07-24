#!/usr/bin/env bash
set -euo pipefail
ROOT="${PROJECT_ROOT:-$(pwd)}"; PYTHON_BIN="${PYTHON_BIN:-/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python}"; cd "$ROOT"
failed=0
check(){ label="$1"; shift; if "$@"; then echo "[PASS] $label"; else echo "[FAIL] $label"; failed=$((failed+1)); fi; }
echo '========================================================================'
echo 'JARVIS — GENESIS VI-A6.5 EXECUTIVE RECOVERY ENGINE'
echo '========================================================================'
check 'Genesis VI-A6.5 package compilation' "$PYTHON_BIN" -m compileall -q core/executive/persistence/recovery.py
check 'Genesis VI-A6.5 unit tests' env PYTHONPATH="$ROOT" "$PYTHON_BIN" -m unittest -v tests.test_genesis_vi_a65_recovery_engine
check 'Genesis VI-A6.5 structural verification' env PYTHONPATH="$ROOT" "$PYTHON_BIN" dev/verification/verify_genesis_vi_a65.py
for f in dev/verify_genesis_vi_a64.sh dev/verify_genesis_vi_a63.sh dev/verify_genesis_vi_a62.sh dev/verify_genesis_vi_a61.sh; do [[ -x "$f" ]] && check "Regression: $(basename "$f")" env PYTHONPATH="$ROOT" PYTHON_BIN="$PYTHON_BIN" "$f" || true; done
echo '------------------------------------------------------------------------'; echo "Checks failed : $failed"; [[ $failed -eq 0 ]] && echo 'Overall status: EXCELLENT' || echo 'Overall status: FAILED'; echo '========================================================================'; exit "$failed"
