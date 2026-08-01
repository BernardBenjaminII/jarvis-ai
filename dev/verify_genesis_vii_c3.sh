#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
export PYTHONPATH="${ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
cd "${ROOT}"
"${PYTHON_BIN}" -m unittest tests.test_genesis_vii_c3_constitutional_ratification
"${PYTHON_BIN}" dev/verification/verify_genesis_vii_c3_constitutional_ratification.py
