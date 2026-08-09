#!/usr/bin/env bash
set -euo pipefail
PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" -m py_compile core/retrieval/semantic_index/context_adaptation.py \
 core/retrieval/semantic_index/store_context.py \
 core/retrieval/semantic_index/service_context.py \
 dev/run_genesis_x_b1_1b.py tests/test_genesis_x_b1_1b.py
"$PYTHON_BIN" -m unittest -v tests.test_genesis_x_b1_1b
"$PYTHON_BIN" -m dev.run_genesis_x_b1_1b audit
echo "[PASS] Genesis X-B1.1b verification"
