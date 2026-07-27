#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
cd "$PROJECT_ROOT"

echo "========================================================================"
echo "GENESIS VII-C1 — CONSTITUTIONAL EXTRACTION ENGINE"
echo "========================================================================"

"$PYTHON_BIN" -m unittest tests.test_genesis_vii_c1_constitutional_extraction
"$PYTHON_BIN" dev/verification/verify_genesis_vii_c1_constitutional_extraction.py
