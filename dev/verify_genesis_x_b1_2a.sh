#!/usr/bin/env bash
set -euo pipefail
PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" -m py_compile \
 core/retrieval/semantic_index/context_router.py \
 core/retrieval/semantic_index/service_context_router.py \
 core/retrieval/semantic_index/service_scale_rev2.py \
 dev/run_genesis_x_b1_2a.py \
 tests/test_genesis_x_b1_2a.py
"$PYTHON_BIN" -m unittest -v tests.test_genesis_x_b1_2a
"$PYTHON_BIN" -m dev.run_genesis_x_b1_2a audit
echo "[PASS] Genesis X-B1.2a verification"
