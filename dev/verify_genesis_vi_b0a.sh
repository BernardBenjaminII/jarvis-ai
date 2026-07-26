#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "$PROJECT_ROOT"

echo "========================================================================"
echo "JARVIS — GENESIS VI-B0A PROJECTION COMPATIBILITY CERTIFICATION"
echo "========================================================================"

"$PYTHON_BIN" -m py_compile \
    core/integration/service.py \
    tests/test_genesis_vi_b0_projection_plane.py \
    tests/test_genesis_vi_b0a_projection_compatibility.py \
    tests/test_genesis_ui_a2_executive_projection_framework.py \
    dev/verification/verify_genesis_vi_b0a_projection_compatibility.py \
    core/integration/bootstrap.py \
    core/src/routes/operations.py \
    core/src/main.py
echo "[PASS] Python compilation"

"$PYTHON_BIN" -m unittest -v \
    tests.test_genesis_vi_b0_projection_plane \
    tests.test_genesis_vi_b0a_projection_compatibility \
    tests.test_genesis_ui_a2_executive_projection_framework

"$PYTHON_BIN" \
    dev/verification/verify_genesis_vi_b0a_projection_compatibility.py

echo
echo "------------------------------------------------------------------------"
echo "Checks failed : 0"
echo "Overall status: EXCELLENT"
echo "========================================================================"
