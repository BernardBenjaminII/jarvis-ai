#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "$PROJECT_ROOT"

echo "========================================================================"
echo "JARVIS — GENESIS VI-B0 EXECUTIVE PROJECTION PLANE"
echo "========================================================================"

"$PYTHON_BIN" -m py_compile \
    core/integration/contracts.py \
    core/integration/errors.py \
    core/integration/registry.py \
    core/integration/service.py \
    core/integration/__init__.py \
    core/integration/providers/operations.py \
    core/integration/providers/capabilities.py \
    core/integration/providers/knowledge.py \
    core/integration/bootstrap.py \
    core/src/routes/operations.py \
    core/src/main.py \
    tests/test_genesis_vi_b0_projection_plane.py \
    tests/test_genesis_vi_b0a_projection_compatibility.py \
    tests/test_genesis_ui_a2_executive_projection_framework.py \
    dev/verification/verify_genesis_vi_b0_projection_plane.py \
    dev/verification/verify_genesis_vi_b0a_projection_compatibility.py
echo "[PASS] Python compilation"

"$PYTHON_BIN" -m unittest -v \
    tests.test_genesis_vi_b0_projection_plane \
    tests.test_genesis_vi_b0a_projection_compatibility \
    tests.test_genesis_ui_a2_executive_projection_framework

"$PYTHON_BIN" \
    dev/verification/verify_genesis_vi_b0_projection_plane.py

"$PYTHON_BIN" \
    dev/verification/verify_genesis_vi_b0a_projection_compatibility.py

echo
echo "[INFO] Running available Integration regressions..."
mapfile -t REGRESSION_MODULES < <(
    find tests -maxdepth 1 -type f \
        \( -iname '*integration*.py' -o -iname '*projection*.py' \) \
        ! -name 'test_genesis_vi_b0_projection_plane.py' \
        ! -name 'test_genesis_vi_b0a_projection_compatibility.py' \
        ! -name 'test_genesis_ui_a2_executive_projection_framework.py' \
        -printf '%f\n' |
    sed -E 's/\.py$//' |
    sort |
    sed 's/^/tests./'
)

if ((${#REGRESSION_MODULES[@]})); then
    "$PYTHON_BIN" -m unittest -v "${REGRESSION_MODULES[@]}"
else
    echo "[INFO] No additional Integration regressions discovered"
fi

echo
echo "------------------------------------------------------------------------"
echo "Checks failed : 0"
echo "Overall status: EXCELLENT"
echo "========================================================================"
