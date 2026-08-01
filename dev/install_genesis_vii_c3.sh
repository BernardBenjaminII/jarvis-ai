#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
export PYTHONPATH="${ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
cd "${ROOT}"
test -f artifacts/audit/km0000-c2/constitutional_analysis.json || { echo "[FAIL] Missing C2 analysis artifact"; exit 1; }
test -f artifacts/audit/km0000-c2/constitutional_graph.json || { echo "[FAIL] Missing C2 graph artifact"; exit 1; }
"${PYTHON_BIN}" -m py_compile core/governance/constitution/ratification/*.py tests/test_genesis_vii_c3_constitutional_ratification.py dev/verification/verify_genesis_vii_c3_constitutional_ratification.py
echo "[PASS] Genesis VII-C3 Python compilation"
"${ROOT}/dev/verify_genesis_vii_c3.sh"
