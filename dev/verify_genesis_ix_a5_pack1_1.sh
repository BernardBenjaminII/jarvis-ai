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
echo "GENESIS IX-A5 PACK 1.1"
echo "CANONICAL RUNTIME BOOTSTRAP REPAIR"
echo "========================================================================"

run_check "Compilation" \
    "${PYTHON_BIN}" -m py_compile \
        dev/runtime/*.py \
        dev/run_genesis_ix_a5_pack1_audit.py \
        dev/certify_genesis_ix_a5_pack1_1.py \
        tests/test_genesis_ix_a5_pack1_1_bootstrap.py

run_check "Bootstrap tests" \
    "${PYTHON_BIN}" -m unittest -v \
        tests.test_genesis_ix_a5_pack1_1_bootstrap

run_check "Bootstrap certification" \
    "${PYTHON_BIN}" -m \
        dev.certify_genesis_ix_a5_pack1_1

run_check "Pack 1 live regression" \
    "${PYTHON_BIN}" -m \
        dev.run_genesis_ix_a5_pack1_audit

run_check "Acceptance harness regression" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/verify_genesis_ix_a4_8_pack2.sh

run_check "Architecture document" \
    test -s \
        docs/architecture/genesis_ix_a5_pack1_1_canonical_runtime_bootstrap.md

run_check "Certification report" \
    test -s \
        docs/audits/genesis_ix_a5_pack1_1/bootstrap_certification.md

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
