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
echo "GENESIS IX-A5 PACK 2"
echo "ENGINEERING REPORT FRAMEWORK"
echo "========================================================================"

run_check "Compilation" \
    "${PYTHON_BIN}" -m py_compile \
        dev/reports/*.py \
        dev/migrations/migrate_genesis_ix_a5_reports.py \
        dev/certify_genesis_ix_a5_pack2.py \
        tests/test_genesis_ix_a5_pack2_reports.py

run_check "Report framework tests" \
    "${PYTHON_BIN}" -m unittest -v \
        tests.test_genesis_ix_a5_pack2_reports

run_check "Report framework certification" \
    "${PYTHON_BIN}" -m \
        dev.certify_genesis_ix_a5_pack2

run_check "Apply IX-A5 report migration" \
    "${PYTHON_BIN}" -m \
        dev.migrations.migrate_genesis_ix_a5_reports

run_check "Migrated runner compilation" \
    "${PYTHON_BIN}" -m py_compile \
        dev/run_genesis_ix_a5_pack1_audit.py

run_check "Bootstrap regression" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/verify_genesis_ix_a5_pack1_1.sh

run_check "Retrieval audit report" \
    test -s \
        docs/audits/genesis_ix_a5_pack1/retrieval_audit.md

run_check "Architecture document" \
    test -s \
        docs/architecture/genesis_ix_a5_pack2_engineering_report_framework.md

run_check "Framework certification report" \
    test -s \
        docs/audits/genesis_ix_a5_pack2/framework_certification.md

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
