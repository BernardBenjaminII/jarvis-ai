#!/usr/bin/env bash
set -euo pipefail
ROOT="${JARVIS_PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "$ROOT"
"$PYTHON_BIN" dev/verification/verify_genesis_vi_a68_part_b.py
