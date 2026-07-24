#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "${PROJECT_ROOT}"

echo
echo "======================================================================"
echo "JARVIS GENESIS IV-A3 — CLAIM CONSTRUCTION VERIFICATION"
echo "======================================================================"

"${PYTHON_BIN}" -m compileall -q core/cognition

"${PYTHON_BIN}" \
    dev/verification/verify_genesis_4a3_claim_construction.py
