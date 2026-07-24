#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "$PROJECT_ROOT"
PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}" \
  "$PYTHON_BIN" dev/verification/verify_convergence_c2.py
