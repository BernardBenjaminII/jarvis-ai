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
echo "GENESIS IX-A5.6 PACK 1"
echo "METADATA JOIN AND LINEAGE AUDIT"
echo "========================================================================"

run_check "Compilation" \
    "${PYTHON_BIN}" -m py_compile \
        dev/metadata_lineage/*.py \
        dev/run_genesis_ix_a5_6_pack1_lineage_audit.py \
        dev/certify_genesis_ix_a5_6_pack1.py \
        tests/test_genesis_ix_a5_6_pack1_lineage.py

run_check "Lineage tests" \
    "${PYTHON_BIN}" -m unittest -v \
        tests.test_genesis_ix_a5_6_pack1_lineage

run_check "Lineage certification" \
    "${PYTHON_BIN}" -m \
        dev.certify_genesis_ix_a5_6_pack1

run_check "Live lineage audit" \
    "${PYTHON_BIN}" -m \
        dev.run_genesis_ix_a5_6_pack1_lineage_audit

run_check "Audit JSON" \
    test -s \
        docs/audits/genesis_ix_a5_6_pack1/metadata_lineage_audit.json

run_check "Audit Markdown" \
    test -s \
        docs/audits/genesis_ix_a5_6_pack1/metadata_lineage_audit.md

run_check "Table profiles" \
    test -s \
        docs/audits/genesis_ix_a5_6_pack1/table_profiles.md

run_check "Architecture document" \
    test -s \
        docs/architecture/genesis_ix_a5_6_pack1_metadata_join_lineage_audit.md

echo "------------------------------------------------------------------------"
echo "Checks passed : ${passed}"
echo "Checks failed : ${failed}"

[[ ${failed} -eq 0 ]] \
    && echo "Overall Status : EXCELLENT" \
    || echo "Overall Status : FAILED"

echo "========================================================================"
[[ ${failed} -eq 0 ]]
