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
echo "GENESIS IX-A5 PACK 4"
echo "SUBJECT QUALIFICATION TRACE"
echo "========================================================================"

run_check "Compilation" \
    "${PYTHON_BIN}" -m py_compile \
        dev/subject_trace/*.py \
        dev/run_genesis_ix_a5_pack4_subject_trace.py \
        dev/certify_genesis_ix_a5_pack4.py \
        tests/test_genesis_ix_a5_pack4_subject_trace.py

run_check "Subject trace tests" \
    "${PYTHON_BIN}" -m unittest -v \
        tests.test_genesis_ix_a5_pack4_subject_trace

run_check "Subject trace certification" \
    "${PYTHON_BIN}" -m \
        dev.certify_genesis_ix_a5_pack4

run_check "Live subject trace" \
    "${PYTHON_BIN}" -m \
        dev.run_genesis_ix_a5_pack4_subject_trace

run_check "Pack 3R regression" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/verify_genesis_ix_a5_pack3r.sh

run_check "Subject trace JSON" \
    test -s \
        docs/audits/genesis_ix_a5_pack4/subject_trace.json

run_check "Subject trace Markdown" \
    test -s \
        docs/audits/genesis_ix_a5_pack4/subject_trace.md

run_check "Architecture document" \
    test -s \
        docs/architecture/genesis_ix_a5_pack4_subject_qualification_trace.md

echo "------------------------------------------------------------------------"
echo "Checks passed : ${passed}"
echo "Checks failed : ${failed}"

[[ ${failed} -eq 0 ]] \
    && echo "Overall Status : EXCELLENT" \
    || echo "Overall Status : FAILED"

echo "========================================================================"

[[ ${failed} -eq 0 ]]
