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
echo "GENESIS IX-A4.7 PACK 2A"
echo "CANONICAL QUALIFIED SEARCH RUNTIME"
echo "========================================================================"

run_check "Compilation" \
    "${PYTHON_BIN}" -m py_compile \
        core/knowledge_catalog/qualified_search.py \
        tests/test_genesis_ix_a4_7_pack2a_canonical_qualified_search.py

run_check "Canonical runtime tests" \
    "${PYTHON_BIN}" -m unittest -v \
        tests.test_genesis_ix_a4_7_pack2a_canonical_qualified_search

run_check "Canonical runtime certification" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/certify_genesis_ix_a4_7_pack2a.sh

run_check "IX-A4.5 Pack 3A.2 regression" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/verify_genesis_ix_a4_5_pack3a_2.sh

run_check "IX-A4.7 Pack 1 regression" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/verify_genesis_ix_a4_7_pack1.sh

run_check "Architecture document" \
    test -s \
        docs/architecture/genesis_ix_a4_7_pack2a_canonical_qualified_search_runtime.md

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
