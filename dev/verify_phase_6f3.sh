#!/usr/bin/env bash

set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"

echo
echo "======================================================================"
echo "JARVIS GEN 2 — PHASE VI-F3 RUNNER COMPOSITION CONTRACTS"
echo "======================================================================"

"$PYTHON_BIN" -m py_compile \
knowledge_engine/assimilation/runner.py

"$PYTHON_BIN" \
-m dev.tests.test_runner_services

echo
echo "----------------------------------------------------------------------"
echo "Checks failed : 0"
echo "Overall status: EXCELLENT"
echo "======================================================================"
