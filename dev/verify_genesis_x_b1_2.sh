#!/usr/bin/env bash
set -euo pipefail
PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" -m py_compile \
 core/retrieval/semantic_index/throughput.py \
 core/retrieval/semantic_index/service_scale.py \
 dev/run_genesis_x_b1_2.py \
 tests/test_genesis_x_b1_2.py
"$PYTHON_BIN" -m unittest -v tests.test_genesis_x_b1_2
"$PYTHON_BIN" -m dev.run_genesis_x_b1_2 audit
echo "[PASS] Genesis X-B1.2 verification"
