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
        printf '[PASS] %s\n' "${label}"
        passed=$((passed + 1))
    else
        printf '[FAIL] %s\n' "${label}"
        failed=$((failed + 1))
    fi
}

printf '%s\n' '========================================================================'
printf '%s\n' 'JARVIS — GENESIS IX-A4.1B PACK 3A'
printf '%s\n' 'EXECUTIVE RUNTIME CERTIFICATION'
printf '%s\n' '========================================================================'

run_check "Pack 3A compilation" \
    "${PYTHON_BIN}" -m py_compile \
        dev/certification/certify_genesis_ix_a4_1b_pack3a_runtime.py \
        tests/test_genesis_ix_a4_1b_pack3a_runtime_certification.py

run_check "Pack 3A unit tests" \
    "${PYTHON_BIN}" -m unittest -v \
        tests.test_genesis_ix_a4_1b_pack3a_runtime_certification

run_check "Executive runtime certification" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/certify_genesis_ix_a4_1b_pack3a.sh

run_check "Certification JSON" \
    test -s \
    docs/audits/genesis_ix_a4_1b_pack3a/executive_runtime_certification.json

run_check "Certification Markdown" \
    test -s \
    docs/audits/genesis_ix_a4_1b_pack3a/executive_runtime_certification.md

run_check "Pack 2 regression" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/verify_genesis_ix_a4_1b_pack2.sh

run_check "Architecture charter" \
    test -s \
    docs/architecture/genesis_ix_a4_1b_pack3a_executive_runtime_certification.md

printf '%s\n' '------------------------------------------------------------------------'
printf 'Checks passed : %d\n' "${passed}"
printf 'Checks failed : %d\n' "${failed}"

if [[ ${failed} -eq 0 ]]; then
    printf '%s\n' 'Overall status: EXCELLENT'
else
    printf '%s\n' 'Overall status: FAILED'
fi

printf '%s\n' '========================================================================'
[[ ${failed} -eq 0 ]]
