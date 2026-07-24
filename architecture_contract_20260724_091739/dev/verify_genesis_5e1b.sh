#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${PROJECT_ROOT}"

echo
echo "========================================================================"
echo "JARVIS GENESIS V-E1B — COGNITION API RESTORATION"
echo "========================================================================"

"${PYTHON_BIN}" dev/verification/verify_genesis_5e1b_cognition_api_restoration.py
