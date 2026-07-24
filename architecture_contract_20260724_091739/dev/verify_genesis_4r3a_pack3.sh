#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${PROJECT_ROOT}"

echo
echo "========================================================================"
echo "JARVIS GENESIS IV-R3A PACK 3 — ARCHITECTURE RECONCILIATION"
echo "========================================================================"

"${PYTHON_BIN}" dev/verification/verify_genesis_4r3a_pack3_architecture_reconciliation.py
