#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$ROOT"
PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" -m py_compile core/retrieval/semantic_index/reliability.py \
 core/retrieval/semantic_index/store_reliability.py \
 core/retrieval/semantic_index/service_reliable.py \
 dev/run_genesis_x_b1_1a.py tests/test_genesis_x_b1_1a.py
"$PYTHON_BIN" -m unittest -v tests.test_genesis_x_b1_1a
"$PYTHON_BIN" -m dev.run_genesis_x_b1_1a audit
echo "[PASS] Genesis X-B1.1a verification"
