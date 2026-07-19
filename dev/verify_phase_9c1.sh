#!/usr/bin/env bash
set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "$PROJECT_ROOT"

PASSED=0
FAILED=0
LOG_FILE="/tmp/jarvis_phase_9c1_check.log"

pass() {
    printf '[PASS] %s\n' "$1"
    PASSED=$((PASSED + 1))
}

fail() {
    printf '[FAIL] %s\n' "$1"
    FAILED=$((FAILED + 1))
}

run_check() {
    local description="$1"
    shift

    if "$@" >"$LOG_FILE" 2>&1; then
        pass "$description"
    else
        fail "$description"
        cat "$LOG_FILE"
    fi
}

echo
echo "======================================================================"
echo "JARVIS GEN 2 — PHASE IX-C1 COGNITIVE ARCHITECTURE INVENTORY"
echo "======================================================================"

run_check \
    "Audit-tool compilation" \
    "$PYTHON_BIN" -m py_compile \
    dev/tools/audit_cognitive_convergence.py \
    dev/verification/verify_cognitive_convergence_inventory.py

run_check \
    "Executive package compilation" \
    "$PYTHON_BIN" -m compileall -q core/executive

run_check \
    "Non-destructive cognitive architecture audit" \
    "$PYTHON_BIN" dev/tools/audit_cognitive_convergence.py \
    --check

run_check \
    "Generated inventory structural verification" \
    "$PYTHON_BIN" \
    dev/verification/verify_cognitive_convergence_inventory.py

run_check \
    "Inventory JSON parses successfully" \
    "$PYTHON_BIN" -m json.tool \
    docs/architecture/convergence/phase_9c1_inventory.json

run_check \
    "No Python cache files under Executive source" \
    bash -c \
    '! find core/executive \( -type d -name "__pycache__" -o -type f -name "*.pyc" \) -print -quit | grep -q .'

run_check \
    "Audit contains all planning candidates" \
    "$PYTHON_BIN" -c '
import json
from pathlib import Path

path = Path(
    "docs/architecture/convergence/"
    "phase_9c1_inventory.json"
)
data = json.loads(path.read_text(encoding="utf-8"))

expected = {
    "core/executive/planner.py",
    "core/executive/planning",
    "core/executive/planning_engine",
}

actual = set(data["planning_locations"])

missing = expected - actual

if missing:
    raise SystemExit(
        "Missing planning candidates: "
        + ", ".join(sorted(missing))
    )
'

echo "----------------------------------------------------------------------"
printf 'Checks passed : %d\n' "$PASSED"
printf 'Checks failed : %d\n' "$FAILED"

if [ "$FAILED" -eq 0 ]; then
    echo "Overall status: EXCELLENT"
    echo "======================================================================"
    exit 0
fi

echo "Overall status: FAILED"
echo "======================================================================"
exit 1
