#!/usr/bin/env bash
set -euo pipefail
PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" -m py_compile core/knowledge_catalog/advanced_extraction/*.py dev/run_genesis_x_a2.py dev/certify_genesis_x_a2.py tests/test_genesis_x_a2.py
"$PYTHON_BIN" -m unittest -v tests.test_genesis_x_a2
"$PYTHON_BIN" -m dev.certify_genesis_x_a2
"$PYTHON_BIN" -m dev.run_genesis_x_a2 --help >/dev/null
echo '[PASS] Genesis X-A2 verification'
