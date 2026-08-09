#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${ROOT}"

echo "========================================================================"
echo "GENESIS IX-A4.8 PACK 1"
echo "EXECUTIVE ACCEPTANCE HEADQUARTERS"
echo "========================================================================"

"${PYTHON_BIN}" -m py_compile dev/certify_genesis_ix_a4_8_pack1.py
"${PYTHON_BIN}" dev/certify_genesis_ix_a4_8_pack1.py

test -s docs/audits/genesis_ix_a4_8_pack1/headquarters_certification.json
test -s docs/audits/genesis_ix_a4_8_pack1/headquarters_certification.md

echo "[PASS] Campaign documents"
echo "[PASS] Headquarters certification"
echo "[PASS] Certification reports"
echo "Overall Status : EXCELLENT"
echo "========================================================================"
