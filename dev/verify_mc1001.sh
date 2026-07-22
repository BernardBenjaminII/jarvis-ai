#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "$PROJECT_ROOT"

echo "======================================================================"
echo "JARVIS — MC-1001 SPRINT 0 EXECUTIVE OPERATIONS INTERFACE"
echo "======================================================================"

"$PYTHON_BIN" dev/verification/verify_mc1001.py
