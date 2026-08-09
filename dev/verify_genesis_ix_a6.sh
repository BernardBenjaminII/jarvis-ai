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
echo "GENESIS IX-A6"
echo "FULL CORPUS MATERIALIZATION CAMPAIGN"
echo "========================================================================"

check "Compilation" \
    "$PYTHON_BIN" -m py_compile \
        core/knowledge_catalog/materialization_campaign/*.py \
        dev/run_genesis_ix_a6_materialization.py \
        dev/certify_genesis_ix_a6.py \
        tests/test_genesis_ix_a6_materialization_campaign.py

check "Unit tests" \
    "$PYTHON_BIN" -m unittest -v \
        tests.test_genesis_ix_a6_materialization_campaign

check "Certification" \
    "$PYTHON_BIN" -m \
        dev.certify_genesis_ix_a6

check "Campaign CLI help" \
    "$PYTHON_BIN" -m \
        dev.run_genesis_ix_a6_materialization \
        --help

check "Architecture document" \
    test -s \
        docs/architecture/genesis_ix_a6_full_corpus_materialization.md

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
