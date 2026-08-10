#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"

"$PYTHON_BIN" -m py_compile \
  core/retrieval/hybrid_rerank/__init__.py \
  core/retrieval/hybrid_rerank/models.py \
  core/retrieval/hybrid_rerank/query.py \
  core/retrieval/hybrid_rerank/dedup.py \
  core/retrieval/hybrid_rerank/scoring.py \
  core/retrieval/hybrid_rerank/service.py \
  dev/run_genesis_x_b2_2.py \
  tests/retrieval/test_genesis_x_b2_2.py

"$PYTHON_BIN" -m unittest -v tests.retrieval.test_genesis_x_b2_2

"$PYTHON_BIN" -m dev.run_genesis_x_b2_2 audit

echo "[PASS] Genesis X-B2.2 verification"
