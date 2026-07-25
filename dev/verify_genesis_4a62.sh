#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHON_BIN="${PYTHON_BIN:-python}"
FAILED=0
pass(){ echo "[PASS] $1"; }
fail(){ echo "[FAIL] $1"; FAILED=$((FAILED+1)); }
echo "========================================================================"
echo "JARVIS — GENESIS IV-A6.2 EXECUTIVE ALTERNATIVE GENERATION"
echo "========================================================================"
"$PYTHON_BIN" dev/verification/verify_genesis_iv_a62.py || FAILED=$((FAILED+1))
if "$PYTHON_BIN" -m py_compile core/cognition/coa/*.py tests/test_genesis_iv_a62_executive_alternative_generation.py; then pass "Python compilation"; else fail "Python compilation"; fi
if "$PYTHON_BIN" -m unittest -v tests.test_genesis_iv_a62_executive_alternative_generation; then pass "Genesis IV-A6.2 unit tests"; else fail "Genesis IV-A6.2 unit tests"; fi
echo "------------------------------------------------------------------------"
echo "Checks failed : $FAILED"
if [[ "$FAILED" -eq 0 ]]; then echo "Overall status: EXCELLENT"; else echo "Overall status: FAILED"; fi
echo "========================================================================"
exit "$FAILED"
