#!/usr/bin/env bash
set -euo pipefail
PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" -m py_compile \
 core/retrieval/semantic_index/store_context_rev3.py \
 core/retrieval/semantic_index/service_context_rev3.py \
 dev/run_genesis_x_b1_2b_rev2.py \
 tests/test_genesis_x_b1_2b_rev2.py
"$PYTHON_BIN" -m unittest -v tests.test_genesis_x_b1_2b_rev2
"$PYTHON_BIN" -m dev.run_genesis_x_b1_2b_rev2 audit
echo "[PASS] Genesis X-B1.2b Revision 2 verification"
