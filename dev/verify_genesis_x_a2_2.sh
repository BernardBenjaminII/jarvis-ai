#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "$ROOT"
"$PYTHON_BIN" -m py_compile core/knowledge_catalog/corpus_hygiene/*.py \
 dev/run_genesis_x_a2_2.py dev/certify_genesis_x_a2_2.py tests/test_genesis_x_a2_2.py
"$PYTHON_BIN" -m unittest -v tests.test_genesis_x_a2_2
"$PYTHON_BIN" -m dev.certify_genesis_x_a2_2
"$PYTHON_BIN" -m dev.run_genesis_x_a2_2 --help >/dev/null
echo "[PASS] Genesis X-A2.2 verification"
