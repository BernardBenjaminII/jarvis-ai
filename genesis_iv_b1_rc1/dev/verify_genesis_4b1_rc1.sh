#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_ROOT"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "========================================================================"
echo "JARVIS — GENESIS IV-B1 RC1 EXECUTIVE INTEGRATION AND VISIBILITY FABRIC"
echo "========================================================================"

"$PYTHON_BIN" -m py_compile \
    core/integration/*.py \
    dev/verification/verify_genesis_iv_b1_rc1.py \
    tests/test_genesis_iv_b1_executive_integration_visibility_fabric.py
echo "[PASS] Python compilation"

"$PYTHON_BIN" -m unittest -v \
    tests.test_genesis_iv_b1_executive_integration_visibility_fabric

"$PYTHON_BIN" dev/verification/verify_genesis_iv_b1_rc1.py

echo "Checks failed : 0"
echo "Overall status: EXCELLENT"
echo "========================================================================"
