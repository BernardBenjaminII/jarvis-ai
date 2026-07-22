#!/usr/bin/env bash
set -Eeuo pipefail
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python}"
export PROJECT_ROOT PYTHONPATH="${PROJECT_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
cd "$PROJECT_ROOT"
failed=0
run(){ local label="$1"; shift; if "$@"; then echo "[PASS] $label"; else echo "[FAIL] $label"; failed=$((failed+1)); fi; }
echo '======================================================================'
echo 'JARVIS — GENESIS VI-A6.4 EXECUTIVE INTEGRITY ENGINE'
echo '======================================================================'
run 'VI-A6.4 package compilation' "$PYTHON_BIN" -m compileall -q core/executive/persistence
run 'VI-A6.4 unit tests' "$PYTHON_BIN" -m unittest -v tests.test_genesis_vi_a64_integrity_engine
run 'VI-A6.4 structural verification' "$PYTHON_BIN" dev/verification/verify_genesis_vi_a64.py
for script in dev/verify_genesis_vi_a63.sh dev/verify_genesis_vi_a62.sh dev/verify_genesis_vi_a61.sh; do
  if [[ -f "$script" ]]; then run "$(basename "$script") regression" bash "$script"; else echo "[SKIP] $(basename "$script") not present"; fi
done
echo '----------------------------------------------------------------------'
echo "Checks failed : $failed"
if [[ $failed -eq 0 ]]; then echo 'Overall status: EXCELLENT'; exit 0; fi
echo 'Overall status: FAILED'; exit 1
