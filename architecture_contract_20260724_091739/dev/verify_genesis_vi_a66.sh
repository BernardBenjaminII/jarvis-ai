#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
PYTHON_BIN="${PYTHON_BIN:-/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python}"

cd "$PROJECT_ROOT"

checks_failed=0

run_check() {
    local label="$1"
    shift
    if "$@"; then
        echo "[PASS] $label"
    else
        echo "[FAIL] $label"
        checks_failed=$((checks_failed + 1))
    fi
}

echo
echo "========================================================================"
echo "JARVIS — GENESIS VI-A6.6 EXECUTIVE LIFECYCLE & SESSION MANAGER"
echo "========================================================================"

run_check \
    "Genesis VI-A6.6 package compilation" \
    "$PYTHON_BIN" -m compileall -q core/executive/lifecycle

run_check \
    "Genesis VI-A6.6 unit tests" \
    env PYTHONPATH="$PROJECT_ROOT" \
    "$PYTHON_BIN" -m unittest -v \
    tests.test_genesis_vi_a66_executive_lifecycle

run_check \
    "Genesis VI-A6.6 structural verification" \
    env PYTHONPATH="$PROJECT_ROOT" \
    "$PYTHON_BIN" dev/verification/verify_genesis_vi_a66.py

for regression in \
    dev/verify_genesis_vi_a65.sh \
    dev/verify_genesis_vi_a64.sh \
    dev/verify_genesis_vi_a63.sh
do
    if [ -x "$regression" ]; then
        run_check \
            "Regression: $(basename "$regression")" \
            env PYTHONPATH="$PROJECT_ROOT" \
            PYTHON_BIN="$PYTHON_BIN" \
            "$regression"
    else
        echo "[SKIP] Regression wrapper absent: $regression"
    fi
done

echo
echo "------------------------------------------------------------------------"
echo "Checks failed : $checks_failed"

if [ "$checks_failed" -eq 0 ]; then
    echo "Overall status: EXCELLENT"
else
    echo "Overall status: FAILED"
fi

echo "========================================================================"

exit "$checks_failed"
