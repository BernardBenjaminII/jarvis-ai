#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${ROOT}"

passed=0
failed=0

run_check() {
    local label="$1"
    shift

    if "$@"; then
        echo "[PASS] ${label}"
        passed=$((passed + 1))
    else
        echo "[FAIL] ${label}"
        failed=$((failed + 1))
    fi
}

echo "========================================================================"
echo "GENESIS IX-A4.7 PACK 1"
echo "EXECUTIVE CONVERSATION GROUNDED ANSWER RUNTIME INTERFACE"
echo "========================================================================"

run_check "Compilation" \
    "${PYTHON_BIN}" -m py_compile \
        core/conversation/grounded_answer/*.py \
        tests/test_genesis_ix_a4_7_pack1_runtime_interface.py

run_check "Runtime interface tests" \
    "${PYTHON_BIN}" -m unittest -v \
        tests.test_genesis_ix_a4_7_pack1_runtime_interface

run_check "Runtime interface certification" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/certify_genesis_ix_a4_7_pack1.sh

run_check "IX-A4.6 regression" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/verify_genesis_ix_a4_6.sh

run_check "Architecture document" \
    test -s \
        docs/architecture/genesis_ix_a4_7_pack1_runtime_interface.md

echo "------------------------------------------------------------------------"
echo "Checks passed : ${passed}"
echo "Checks failed : ${failed}"

if [[ ${failed} -eq 0 ]]; then
    echo "Overall Status : EXCELLENT"
else
    echo "Overall Status : FAILED"
fi

echo "========================================================================"
[[ ${failed} -eq 0 ]]
