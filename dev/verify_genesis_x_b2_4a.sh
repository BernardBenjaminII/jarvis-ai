#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python}"

echo "============================================================"
echo " GENESIS X-B2.4A — SYNTHESIS QUALITY HARDENING VERIFICATION"
echo "============================================================"

"$PYTHON_BIN" -m py_compile \
  core/retrieval/evidence_grounding/focus.py \
  core/retrieval/evidence_grounding/service.py \
  core/retrieval/evidence_grounding/adapter.py \
  dev/run_genesis_x_b2_4a.py

"$PYTHON_BIN" -m unittest \
  tests.retrieval.test_genesis_x_b2_4 \
  tests.retrieval.test_genesis_x_b2_4a \
  -v

"$PYTHON_BIN" -m dev.run_genesis_x_b2_4a certify

echo
echo "============================================================"
echo " GENESIS X-B2.4A VERIFICATION COMPLETE"
echo "============================================================"
