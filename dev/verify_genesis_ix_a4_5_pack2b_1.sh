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
echo "GENESIS IX-A4.5 PACK 2B.1"
echo "LEXICAL QUALIFICATION NORMALIZATION REPAIR"
echo "========================================================================"

run_check "Compilation" \
    "${PYTHON_BIN}" -m py_compile \
        core/retrieval/qualification/lexical.py \
        tests/test_genesis_ix_a4_5_pack2b_1_lexical_normalization.py

run_check "Lexical normalization tests" \
    "${PYTHON_BIN}" -m unittest -v \
        tests.test_genesis_ix_a4_5_pack2b_1_lexical_normalization

run_check "Lexical normalization certification" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/certify_genesis_ix_a4_5_pack2b_1.sh

run_check "Qualification engine regression" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/verify_genesis_ix_a4_5_pack2a.sh

run_check "Native semantic fixture regression" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/verify_genesis_ix_a4_5_pack3a_2.sh

run_check "Architecture document" \
    test -s \
        docs/architecture/genesis_ix_a4_5_pack2b_1_lexical_normalization_repair.md

echo "------------------------------------------------------------------------"
echo "Checks passed : ${passed}"
echo "Checks failed : ${failed}"
[[ ${failed} -eq 0 ]] && echo "Overall Status : EXCELLENT" || echo "Overall Status : FAILED"
echo "========================================================================"
[[ ${failed} -eq 0 ]]
