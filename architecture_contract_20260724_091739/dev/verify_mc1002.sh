#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
"${PYTHON_BIN:-python3}" dev/verification/verify_mc1002.py
