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
printf '%s\n' 'JARVIS — GENESIS IX-A4.1B PACK 3A.1'
printf '%s\n' 'CERTIFICATION RUNTIME BOOTSTRAP'
printf '%s\n' '========================================================================'

run_check "Compilation" \
    "${PYTHON_BIN}" -m py_compile \
        core/certification/runtime/contracts.py \
        core/certification/runtime/discovery.py \
        core/certification/runtime/imports.py \
        core/certification/runtime/bootstrap.py \
        dev/certification/certify_runtime_bootstrap.py \
        dev/certification/repair_pack3a_bootstrap.py \
        tests/test_genesis_ix_a4_1b_pack3a_1_runtime_bootstrap.py

run_check "Unit tests" \
    "${PYTHON_BIN}" -m unittest -v \
        tests.test_genesis_ix_a4_1b_pack3a_1_runtime_bootstrap

run_check "Repair Pack 3A bootstrap" \
    "${PYTHON_BIN}" -m \
        dev.certification.repair_pack3a_bootstrap

run_check "Certification runtime bootstrap" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/certify_genesis_ix_a4_1b_pack3a_1.sh

for report in \
    runtime_environment.md \
    module_resolution.md \
    repository_layout.md \
    bootstrap_trace.md \
    runtime_bootstrap.json
do
    run_check "Report ${report}" \
        test -s "docs/audits/certification_runtime/${report}"
done

run_check "Pack 3A retry" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/certify_genesis_ix_a4_1b_pack3a.sh

run_check "Pack 2 regression" \
    env PYTHON_BIN="${PYTHON_BIN}" \
    ./dev/verify_genesis_ix_a4_1b_pack2.sh

run_check "Architecture charter" \
    test -s \
        docs/architecture/genesis_ix_a4_1b_pack3a_1_certification_runtime_bootstrap.md

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
