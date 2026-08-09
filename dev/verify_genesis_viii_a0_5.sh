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

printf '%s\n' '========================================================================'
printf '%s\n' 'JARVIS — GENESIS VIII-A0-5'
printf '%s\n' 'EXECUTIVE INTEGRATION CONTRACTS'
printf '%s\n' '========================================================================'

run_check "VIII-A0-4 prerequisite" \
    env PYTHON_BIN="${PYTHON_BIN}" ./dev/verify_genesis_viii_a0_4.sh

run_check "Executive integration package compilation" \
    "${PYTHON_BIN}" -m compileall -q core/government/executive

run_check "Executive integration contract tests" \
    "${PYTHON_BIN}" -m unittest -v \
        tests.test_genesis_viii_a0_5_executive_integration_contracts

run_check "Public Executive integration API" \
    "${PYTHON_BIN}" - <<'PY'
from core.government import (
    ExecutiveGovernmentProvider,
    OrganizationalSupervisor,
    GovernmentAssessmentProvider,
    ExecutiveRecommendationProvider,
    DirectiveProvider,
    AssignmentProvider,
    DepartmentReportProvider,
    ExecutiveSnapshotProvider,
    ExecutiveIntegrationProvider,
)
print("OK")
PY

run_check "Contract-only dependency boundary" \
    "${PYTHON_BIN}" - <<'PY'
from pathlib import Path

root = Path("core/government/executive")
for path in root.glob("*.py"):
    source = path.read_text(encoding="utf-8")
    forbidden = (
        "core.executive.director",
        "core.src",
        "fastapi",
        "sqlite3",
        "sqlalchemy",
        "requests",
        "subprocess",
        "asyncio",
    )
    for token in forbidden:
        assert token not in source, f"{path}: forbidden dependency {token}"
print("OK")
PY

run_check "Architecture document exists" \
    test -s docs/architecture/genesis_viii_a0_5_executive_integration_contracts.md

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
