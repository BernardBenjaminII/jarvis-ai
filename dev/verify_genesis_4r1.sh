#!/usr/bin/env bash
set -Eeuo pipefail
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
cd "$PROJECT_ROOT"
"$PYTHON_BIN" -m compileall -q core/cognition/common
"$PYTHON_BIN" dev/verification/verify_genesis_4r1_cognitive_object_model.py
