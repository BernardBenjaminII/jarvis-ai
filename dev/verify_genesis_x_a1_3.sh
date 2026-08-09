#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; PYTHON_BIN="${PYTHON_BIN:-python}"; cd "$ROOT"
"$PYTHON_BIN" -m py_compile dev/materialization_completion_audit/*.py dev/run_genesis_x_a1_3_audit.py dev/certify_genesis_x_a1_3.py tests/test_genesis_x_a1_3.py
"$PYTHON_BIN" -m unittest -v tests.test_genesis_x_a1_3
"$PYTHON_BIN" -m dev.certify_genesis_x_a1_3
"$PYTHON_BIN" -m dev.run_genesis_x_a1_3_audit --help >/dev/null
echo '[PASS] Genesis X-A1.3 verification'
