#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "$ROOT"

"$PYTHON_BIN" -m py_compile \
  core/knowledge_catalog/ocr_recovery/*.py \
  dev/run_genesis_x_a2_1.py \
  dev/certify_genesis_x_a2_1.py \
  tests/test_genesis_x_a2_1.py

"$PYTHON_BIN" -m unittest -v tests.test_genesis_x_a2_1
"$PYTHON_BIN" -m dev.certify_genesis_x_a2_1
"$PYTHON_BIN" -m dev.run_genesis_x_a2_1 --help >/dev/null

echo "[PASS] Genesis X-A2.1 verification"
