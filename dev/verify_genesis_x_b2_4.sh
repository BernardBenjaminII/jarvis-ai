#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="${PROJECT_ROOT:-/media/abdullah/JARVISDATA/Projects/jarvis-ai}"
PYTHON_BIN="${PYTHON_BIN:-/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python}"
cd "$PROJECT_ROOT"
echo "============================================================"
echo " GENESIS X-B2.4 VERIFICATION"
echo "============================================================"
"$PYTHON_BIN" -m unittest tests.retrieval.test_genesis_x_b2_4 -v
"$PYTHON_BIN" -m unittest tests.test_genesis_ix_a4_6_grounded_answer_engine -v
"$PYTHON_BIN" -m dev.run_genesis_x_b2_4 certify
echo "============================================================"
echo " GENESIS X-B2.4 VERIFICATION COMPLETE"
echo "============================================================"
