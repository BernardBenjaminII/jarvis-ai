#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
PYTHON_BIN="${PYTHON_BIN:-python3}"
echo "========================================================================"
echo "JARVIS — GENESIS VII-A0 PACK 4B-1"
echo "MISSION CONTROL EXECUTIVE EVENT TIMELINE PROJECTION"
echo "========================================================================"
"$PYTHON_BIN" dev/verification/verify_genesis_vii_a0_pack4b1.py
