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
echo "GENESIS IX-A5 PACK 3"
echo "QUALIFICATION RECALL FORENSICS"
echo "========================================================================"

run_check "Compilation" \
    "${PYTHON_BIN}" -m py_compile \
        dev/qualification_forensics/*.py \
        dev/run_genesis_ix_a5_pack3_forensics.py \
        dev/certify_genesis_ix_a5_pack3.py \
        tests/test_genesis_ix_a5_pack3_forensics.py

run_check "Forensic tests" \
    "${PYTHON_BIN}" -m unittest -v \
        tests.test_genesis_ix_a5_pack3_forensics

run_check "Forensic certification" \
    "${PYTHON_BIN}" -m \
        dev.certify_genesis_ix_a5_pack3

run_check "Live forensic audit" \
    "${PYTHON_BIN}" -m \
        dev.run_genesis_ix_a5_pack3_forensics

run_check "Pack 2.1 regression" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/verify_genesis_ix_a5_pack2_1.sh

run_check "Forensic JSON" \
    test -s \
        docs/audits/genesis_ix_a5_pack3/qualification_forensics.json

run_check "Forensic Markdown" \
    test -s \
        docs/audits/genesis_ix_a5_pack3/qualification_forensics.md

run_check "Architecture document" \
    test -s \
        docs/architecture/genesis_ix_a5_pack3_qualification_recall_forensics.md

echo "------------------------------------------------------------------------"
echo "Checks passed : ${passed}"
echo "Checks failed : ${failed}"
[[ ${failed} -eq 0 ]] && echo "Overall Status : EXCELLENT" || echo "Overall Status : FAILED"
echo "========================================================================"
[[ ${failed} -eq 0 ]]
