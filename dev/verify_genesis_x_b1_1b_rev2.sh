#!/usr/bin/env bash
set -euo pipefail
PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" -m py_compile core/retrieval/semantic_index/context_tree.py core/retrieval/semantic_index/store_context_rev2.py core/retrieval/semantic_index/service_context_rev2.py dev/run_genesis_x_b1_1b_rev2.py tests/test_genesis_x_b1_1b_rev2.py
"$PYTHON_BIN" -m unittest -v tests.test_genesis_x_b1_1b_rev2
"$PYTHON_BIN" -m dev.run_genesis_x_b1_1b_rev2 audit
echo "[PASS] Genesis X-B1.1b Revision 2 verification"
