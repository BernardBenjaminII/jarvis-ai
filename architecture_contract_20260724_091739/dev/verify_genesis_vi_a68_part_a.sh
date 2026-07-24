#!/usr/bin/env bash
set -euo pipefail
ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PYTHON_BIN="${PYTHON_BIN:-/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python}"
cd "$ROOT"
failed=0
check() {
  local name="$1"; shift
  if "$@"; then echo "[PASS] $name"; else echo "[FAIL] $name"; failed=$((failed + 1)); fi
}

echo "========================================================================"
echo "JARVIS — GENESIS VI-A6.8 PART A TIMELINE REPOSITORY FOUNDATION"
echo "========================================================================"
check "Genesis VI-A6.8 Part A package compilation" \
  "$PYTHON_BIN" -m compileall -q core/executive/timeline tests/test_genesis_vi_a68_part_a_timeline_repository.py
check "Genesis VI-A6.8 Part A unit tests" \
  env PYTHONPATH="$ROOT" "$PYTHON_BIN" -m unittest -v tests.test_genesis_vi_a68_part_a_timeline_repository
check "Genesis VI-A6.8 Part A structural certification" \
  env PYTHONPATH="$ROOT" "$PYTHON_BIN" dev/verification/verify_genesis_vi_a68_part_a.py

if [[ -x dev/verify_genesis_vi_a67.sh ]]; then
  check "Genesis VI-A6.7 regression" \
    env PYTHONPATH="$ROOT" PYTHON_BIN="$PYTHON_BIN" ./dev/verify_genesis_vi_a67.sh
fi

echo "------------------------------------------------------------------------"
echo "Checks failed : $failed"
[[ "$failed" -eq 0 ]] && echo "Overall status: EXCELLENT" || echo "Overall status: FAILED"
echo "========================================================================"
exit "$failed"
