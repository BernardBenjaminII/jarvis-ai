#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"

"$PYTHON_BIN" -m py_compile \
  core/retrieval/vector_search/__init__.py \
  core/retrieval/vector_search/models.py \
  core/retrieval/vector_search/math.py \
  core/retrieval/vector_search/service.py \
  dev/run_genesis_x_b2_1.py \
  tests/retrieval/test_genesis_x_b2_1.py

"$PYTHON_BIN" -m unittest -v tests.retrieval.test_genesis_x_b2_1

"$PYTHON_BIN" -m dev.run_genesis_x_b2_1 audit

echo "[PASS] Genesis X-B2.1 verification"
