#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "========================================================================"
echo "JARVIS — GENESIS IV-A8 EXECUTIVE MISSION COMPILER"
echo "========================================================================"

"$PYTHON_BIN" -m py_compile \
    core/cognition/mission_compiler/*.py \
    dev/verification/verify_genesis_iv_a8.py \
    tests/test_genesis_iv_a8_executive_mission_compiler.py
echo "[PASS] Python compilation"

"$PYTHON_BIN" -m unittest -v \
    tests.test_genesis_iv_a8_executive_mission_compiler

"$PYTHON_BIN" dev/verification/verify_genesis_iv_a8.py

echo "Checks failed : 0"
echo "Overall status: EXCELLENT"
echo "========================================================================"
