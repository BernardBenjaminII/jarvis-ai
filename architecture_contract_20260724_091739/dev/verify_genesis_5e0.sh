#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${PROJECT_ROOT}"

echo
echo "========================================================================"
echo "JARVIS GENESIS V-E0 — ENGINEERING OPERATING SYSTEM FOUNDATION"
echo "========================================================================"
"${PYTHON_BIN}" dev/verification/verify_genesis_5e0_engineering_os_foundation.py
