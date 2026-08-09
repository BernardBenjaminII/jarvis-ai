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
echo "GENESIS IX-A4.5 PACK 3A.1"
echo "KNOWN QUERY CERTIFICATION FIXTURE REPAIR"
echo "========================================================================"

run_check "Compilation" \
    "${PYTHON_BIN}" -m py_compile \
        core/retrieval/certification/semantic_fixture.py \
        dev/certification/repair_genesis_ix_a4_5_pack3a_1.py \
        tests/test_genesis_ix_a4_5_pack3a_1_fixture_repair.py

run_check "Fixture repair tests" \
    "${PYTHON_BIN}" -m unittest -v \
        tests.test_genesis_ix_a4_5_pack3a_1_fixture_repair

run_check "Apply fixture repair" \
    "${PYTHON_BIN}" -m \
        dev.certification.repair_genesis_ix_a4_5_pack3a_1

run_check "Repaired IX-A4.3 compilation" \
    "${PYTHON_BIN}" -m py_compile \
        dev/certification/certify_genesis_ix_a4_3.py

run_check "End-to-end retrieval certification" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/certify_genesis_ix_a4_3.sh

run_check "Pack 3A regression" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/verify_genesis_ix_a4_5_pack3a.sh

run_check "Architecture document" \
    test -s \
        docs/architecture/genesis_ix_a4_5_pack3a_1_known_query_fixture_repair.md

for report in fixture_repair.json fixture_repair.md
do
    run_check "Report ${report}" \
        test -s "docs/audits/genesis_ix_a4_5_pack3a_1/${report}"
done

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
