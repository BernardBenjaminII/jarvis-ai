#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "========================================================================"
echo "JARVIS — GENESIS VII-A0 PACK 4A-3.1"
echo "EXECUTIVE PUBLISHER WIRING"
echo "========================================================================"

"$PYTHON_BIN" dev/verification/verify_genesis_vii_a0_pack4a3_1.py
