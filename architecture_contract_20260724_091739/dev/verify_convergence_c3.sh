#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
echo '========================================================================'
echo 'JARVIS — CONVERGENCE C-3 CAPABILITY ROUTING'
echo '========================================================================'
"$PYTHON_BIN" "$ROOT/dev/verification/verify_convergence_c3.py"
echo '========================================================================'
