#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"; cd "$ROOT"; PYTHON_BIN="${PYTHON_BIN:-python3}"
echo '========================================================================'
echo 'JARVIS — GENESIS IV-A7 EXECUTIVE DECISION ENGINE'
echo '========================================================================'
"$PYTHON_BIN" -m py_compile core/cognition/executive_decision/*.py dev/verification/verify_genesis_iv_a7.py tests/test_genesis_iv_a7_executive_decision_engine.py
echo '[PASS] Python compilation'
"$PYTHON_BIN" -m unittest -v tests.test_genesis_iv_a7_executive_decision_engine
"$PYTHON_BIN" dev/verification/verify_genesis_iv_a7.py
echo 'Checks failed : 0'; echo 'Overall status: EXCELLENT'; echo '========================================================================'
