#!/usr/bin/env bash
set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
LOG_FILE="/tmp/jarvis_phase_x_check.log"
PASSED=0
FAILED=0

cd "$PROJECT_ROOT"

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
echo "JARVIS GEN 2 — PHASE X REASONING ENGINE FOUNDATION"
echo "======================================================================"

run_check \
    "Reasoning package compilation" \
    "$PYTHON_BIN" -m compileall -q core/reasoning

run_check \
    "Reasoning structural boundaries" \
    "$PYTHON_BIN" \
    dev/verification/verify_phase_x_reasoning_foundation.py

run_check \
    "Reasoning foundation unit tests" \
    "$PYTHON_BIN" -m unittest -v \
    tests.test_phase_x_reasoning_foundation

run_check \
    "Stable public reasoning imports" \
    "$PYTHON_BIN" -c '
from core.reasoning import (
    EvidenceItem,
    Hypothesis,
    PlanningRecommendation,
    ReasoningEngine,
    ReasoningRequest,
    ReasoningResult,
)
assert EvidenceItem
assert Hypothesis
assert PlanningRecommendation
assert ReasoningEngine
assert ReasoningRequest
assert ReasoningResult
'

run_check \
    "Deterministic reasoning smoke test" \
    "$PYTHON_BIN" -c '
from tests.test_phase_x_reasoning_foundation import build_request
from core.reasoning import ReasoningEngine
engine = ReasoningEngine()
first = engine.reason(build_request())
second = engine.reason(build_request())
assert first.fingerprint == second.fingerprint
assert first.selected_hypothesis_id == "hypothesis_build_foundation"
assert first.planning_recommendation is not None
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
