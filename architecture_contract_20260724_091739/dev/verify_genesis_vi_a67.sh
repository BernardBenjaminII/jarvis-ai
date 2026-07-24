#!/usr/bin/env bash
set -euo pipefail
ROOT="${PROJECT_ROOT:-$(pwd)}"
PYTHON_BIN="${PYTHON_BIN:-/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python}"
cd "$ROOT"
failed=0
check() { local name="$1"; shift; if "$@"; then echo "[PASS] $name"; else echo "[FAIL] $name"; failed=$((failed+1)); fi; }

echo "========================================================================"
echo "JARVIS — GENESIS VI-A6.7 EXECUTIVE TIMELINE ENGINE"
echo "========================================================================"
check "Genesis VI-A6.7 package compilation" "$PYTHON_BIN" -m compileall -q core/executive/timeline
check "Genesis VI-A6.7 unit tests" env PYTHONPATH="$ROOT" "$PYTHON_BIN" -m unittest -v tests.test_genesis_vi_a67_executive_timeline
check "Genesis VI-A6.7 structural verification" env PYTHONPATH="$ROOT" "$PYTHON_BIN" dev/verification/verify_genesis_vi_a67.py

for r in dev/verify_genesis_vi_a66.sh dev/verify_genesis_vi_a65.sh dev/verify_genesis_vi_a64.sh dev/verify_genesis_vi_a63.sh; do
  [[ -x "$r" ]] && check "Regression: $(basename "$r")" env PYTHONPATH="$ROOT" PYTHON_BIN="$PYTHON_BIN" "$r"
done
echo "------------------------------------------------------------------------"
echo "Checks failed : $failed"
[[ "$failed" -eq 0 ]] && echo "Overall status: EXCELLENT" || echo "Overall status: FAILED"
echo "========================================================================"
exit "$failed"
