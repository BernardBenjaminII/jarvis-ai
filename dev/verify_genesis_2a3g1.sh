#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${PROJECT_ROOT}"

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

printf '%s\n' '======================================================================'
printf '%s\n' 'JARVIS GENESIS II-A3G.1'
printf '%s\n' 'CANONICAL CONSTITUTIONAL ORDERING REPAIR'
printf '%s\n' '======================================================================'

run_check "II-A3G.1 package compilation" \
    "${PYTHON_BIN}" -m py_compile \
        dev/verification/genesis_manifest.py \
        tests/test_genesis_2a3g1_canonical_constitutional_ordering.py

run_check "Canonical ordering tests" \
    "${PYTHON_BIN}" -m unittest -v \
        tests.test_genesis_2a3g1_canonical_constitutional_ordering

run_check "Current Genesis manifest validates" \
    "${PYTHON_BIN}" dev/verification/genesis_manifest.py --check

run_check "IX runtime root precedes capability branch" \
    "${PYTHON_BIN}" - <<'PY'
from dev.verification.genesis_manifest import parse_phase

root = parse_phase("dev/verify_genesis_ix_0.sh")
branch = parse_phase("dev/verify_genesis_ix_a1.sh")
maintenance = parse_phase("dev/verify_genesis_ix_a1_1.sh")

assert root < branch < maintenance
assert root.label == "IX-Z0"
print(root.label, "<", branch.label, "<", maintenance.label)
PY

run_check "Genesis II-A3G regression" \
    env PYTHON_BIN="${PYTHON_BIN}" ./dev/verify_genesis_2a3g.sh

run_check "Architecture document exists" \
    test -s docs/architecture/convergence/genesis_2a3g1_canonical_constitutional_ordering_repair.md

printf '%s\n' '----------------------------------------------------------------------'
printf 'Checks passed : %d\n' "${passed}"
printf 'Checks failed : %d\n' "${failed}"
if [[ ${failed} -eq 0 ]]; then
    printf '%s\n' 'Overall status: EXCELLENT'
else
    printf '%s\n' 'Overall status: FAILED'
fi
printf '%s\n' '======================================================================'

[[ ${failed} -eq 0 ]]
