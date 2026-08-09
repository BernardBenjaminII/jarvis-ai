#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "$ROOT"

"$PYTHON_BIN" -m py_compile \
  core/retrieval/hybrid/*.py \
  dev/run_genesis_x_b1.py \
  tests/test_genesis_x_b1.py

"$PYTHON_BIN" -m unittest -v tests.test_genesis_x_b1
"$PYTHON_BIN" -m dev.run_genesis_x_b1 audit

echo "[PASS] Genesis X-B1 verification"
