#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="${PROJECT_ROOT:-/media/abdullah/JARVISDATA/Projects/jarvis-ai}"
PYTHON_BIN="${PYTHON_BIN:-/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python}"
cd "$PROJECT_ROOT"
echo '============================================================'
echo ' GENESIS X-B2.4A-1 VERIFICATION'
echo ' UTILITY PROPAGATION & INTENT-AWARE FOCUS'
echo '============================================================'
"$PYTHON_BIN" -m py_compile core/retrieval/evidence_grounding/__init__.py core/retrieval/evidence_grounding/focus.py core/retrieval/evidence_grounding/adapter.py core/retrieval/evidence_grounding/service.py dev/run_genesis_x_b2_4a_1.py tests/retrieval/test_genesis_x_b2_4a_1.py
"$PYTHON_BIN" -m unittest tests.retrieval.test_genesis_x_b2_4 tests.retrieval.test_genesis_x_b2_4a tests.retrieval.test_genesis_x_b2_4a_1 -v
"$PYTHON_BIN" -m dev.run_genesis_x_b2_4a_1 certify
echo '============================================================'
echo ' GENESIS X-B2.4A-1 VERIFICATION COMPLETE'
echo '============================================================'
