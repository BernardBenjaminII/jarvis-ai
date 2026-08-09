#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "$ROOT"

passed=0
failed=0

check() {
    local label="$1"
    shift

    if "$@"; then
        echo "[PASS] $label"
        passed=$((passed + 1))
    else
        echo "[FAIL] $label"
        failed=$((failed + 1))
    fi
}

echo "========================================================================"
echo "GENESIS X-A1.1"
echo "SQLITE RELIABILITY AND RESUME REPAIR"
echo "========================================================================"

check "Compilation" \
    "$PYTHON_BIN" -m py_compile \
        core/knowledge_catalog/production_materialization/*.py \
        dev/repair_genesis_x_a1_1_state.py \
        dev/certify_genesis_x_a1_1.py \
        tests/test_genesis_x_a1_1.py

check "Unit tests" \
    "$PYTHON_BIN" -m unittest -v \
        tests.test_genesis_x_a1_1

check "Certification" \
    "$PYTHON_BIN" -m \
        dev.certify_genesis_x_a1_1

check "State recovery CLI" \
    "$PYTHON_BIN" -m \
        dev.repair_genesis_x_a1_1_state \
        --help

check "Architecture" \
    test -s \
        docs/architecture/genesis_x_a1_1_sqlite_reliability_resume.md

echo "------------------------------------------------------------------------"
echo "Checks passed : $passed"
echo "Checks failed : $failed"

if [[ $failed -eq 0 ]]; then
    echo "Overall Status : EXCELLENT"
else
    echo "Overall Status : FAILED"
fi

echo "========================================================================"

[[ $failed -eq 0 ]]
