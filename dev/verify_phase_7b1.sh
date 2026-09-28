#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python}"

echo "======================================================================"
echo "JARVIS GEN 2 — PHASE VII-B1 DETERMINISTIC SOURCE ADMISSION"
echo "======================================================================"

"$PYTHON_BIN" -m compileall -q     knowledge_engine/acquisition_control     tests/test_phase_7b1_source_admission.py

"$PYTHON_BIN" -m unittest -v     tests.test_phase_7b1_source_admission

env PYTHON_BIN="$PYTHON_BIN" ./dev/verify_phase_7a8.sh

echo "----------------------------------------------------------------------"
echo "Checks failed : 0"
echo "Overall status: EXCELLENT"
echo "======================================================================"
