#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$PROJECT_ROOT"

echo "========================================================================"
echo "JARVIS — EAF-001 EXECUTIVE ACADEMY CONSTITUTIONAL FOUNDATION"
echo "========================================================================"

"$PYTHON_BIN" dev/verification/verify_eaf001.py
