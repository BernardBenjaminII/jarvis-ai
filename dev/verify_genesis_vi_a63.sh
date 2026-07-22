#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"

echo "========================================================================"
echo "JARVIS — GENESIS VI-A6.3 EXECUTIVE CHECKPOINT STORE"
echo "========================================================================"

checks_failed=0

run_check() {
    local description="$1"
    shift
    if "$@"; then
        echo "[PASS] $description"
    else
        echo "[FAIL] $description"
        checks_failed=$((checks_failed + 1))
    fi
}

run_check \
    "Package compilation" \
    "$PYTHON_BIN" -m compileall -q core/executive/persistence

run_check \
    "Genesis VI-A6.3 unit tests" \
    "$PYTHON_BIN" -m unittest -v tests.test_genesis_vi_a63_checkpoint_store

run_check \
    "Genesis VI-A6.3 structural certification" \
    "$PYTHON_BIN" dev/verification/verify_genesis_vi_a63.py

if [[ -x dev/verify_genesis_vi_a62.sh ]]; then
    run_check \
        "Genesis VI-A6.2 regression" \
        env PROJECT_ROOT="$PROJECT_ROOT" PYTHONPATH="$PYTHONPATH" \
            PYTHON_BIN="$PYTHON_BIN" ./dev/verify_genesis_vi_a62.sh
fi

if [[ -x dev/verify_genesis_vi_a61.sh ]]; then
    run_check \
        "Genesis VI-A6.1 regression" \
        env PROJECT_ROOT="$PROJECT_ROOT" PYTHONPATH="$PYTHONPATH" \
            PYTHON_BIN="$PYTHON_BIN" ./dev/verify_genesis_vi_a61.sh
fi

echo
echo "------------------------------------------------------------------------"
echo "Checks failed : $checks_failed"
if [[ "$checks_failed" -eq 0 ]]; then
    echo "Overall status: EXCELLENT"
    echo "========================================================================"
    exit 0
fi

echo "Overall status: FAILED"
echo "========================================================================"
exit 1
