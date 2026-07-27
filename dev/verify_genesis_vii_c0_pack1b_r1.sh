#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
"$PYTHON_BIN" -m py_compile \
  core/governance/audit/models.py core/governance/audit/filesystem.py \
  core/governance/audit/inventory.py core/governance/audit/verification.py \
  core/governance/audit/__init__.py dev/verification/verify_genesis_vii_c0_pack1b_r1.py \
  tests/test_genesis_vii_c0_pack1b_r1.py
"$PYTHON_BIN" dev/verification/verify_genesis_vii_c0_pack1b_r1.py "$@"
