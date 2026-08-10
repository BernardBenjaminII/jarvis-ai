#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"

"$PYTHON_BIN" -m py_compile \
  core/retrieval/evidence_context/__init__.py \
  core/retrieval/evidence_context/models.py \
  core/retrieval/evidence_context/precision.py \
  core/retrieval/evidence_context/dedup.py \
  core/retrieval/evidence_context/service.py \
  dev/run_genesis_x_b2_3.py \
  tests/retrieval/test_genesis_x_b2_3.py

"$PYTHON_BIN" -m unittest -v tests.retrieval.test_genesis_x_b2_3

"$PYTHON_BIN" -m dev.run_genesis_x_b2_3 audit

echo "[PASS] Genesis X-B2.3 verification"
