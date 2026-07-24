#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
echo "========================================================================"
echo "JARVIS — CONVERGENCE C-6 EXECUTIVE OBSERVABILITY & MISSION TRANSPARENCY"
echo "========================================================================"
"$PYTHON_BIN" dev/verification/verify_convergence_c6.py
"$PYTHON_BIN" -m unittest tests.test_convergence_c6_executive_observability
printf '\n[PASS] C-6 deterministic unit tests\n'
