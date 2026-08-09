#!/usr/bin/env bash
set -euo pipefail
PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" -m py_compile core/retrieval/semantic_index/predictive_routing.py \
 core/retrieval/semantic_index/service_scale_opt.py dev/run_genesis_x_b1_2b.py tests/test_genesis_x_b1_2b.py
"$PYTHON_BIN" -m unittest -v tests.test_genesis_x_b1_2b
"$PYTHON_BIN" -m dev.run_genesis_x_b1_2b audit
echo "[PASS] Genesis X-B1.2b verification"
