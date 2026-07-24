#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
cd "$ROOT"
chmod +x dev/verification/verify_genesis_ui_a2_executive_projection_framework.py dev/verify_genesis_ui_a2_executive_projection_framework.sh
PYTHON_BIN="$PYTHON_BIN" ./dev/verify_genesis_ui_a2_executive_projection_framework.sh
echo "[PASS] Genesis UI-A2 Executive Projection Framework installed"
