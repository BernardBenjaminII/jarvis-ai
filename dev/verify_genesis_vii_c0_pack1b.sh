#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
cd "$PROJECT_ROOT"

"$PYTHON_BIN" -m py_compile \
    core/governance/audit/__init__.py \
    core/governance/audit/verification.py \
    dev/verification/verify_genesis_vii_c0_pack1b.py \
    tests/test_genesis_vii_c0_pack1b.py

"$PYTHON_BIN" dev/verification/verify_genesis_vii_c0_pack1b.py "$@"
