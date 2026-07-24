#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
cd "$PROJECT_ROOT"

FAILURES=0
run_check() {
    local label="$1"
    shift
    if "$@"; then
        echo "[PASS] $label"
    else
        echo "[FAIL] $label"
        FAILURES=$((FAILURES + 1))
    fi
}

printf '%s\n' "========================================================================" "JARVIS — GENESIS VI-A3B COMPATIBILITY FINALIZATION" "========================================================================"

run_check "Structural verification" \
    "$PYTHON_BIN" dev/verification/verify_genesis_vi_a3b_compatibility_finalization.py

run_check "Python compilation" \
    "$PYTHON_BIN" -m py_compile \
        core/src/routes/operations.py \
        tests/test_genesis_vi_a3b_compatibility_finalization.py \
        dev/verification/verify_genesis_vi_a3b_compatibility_finalization.py

run_check "VI-A3B unit tests" \
    "$PYTHON_BIN" -m unittest tests.test_genesis_vi_a3b_compatibility_finalization

for regression in \
    dev/verify_genesis_ui_a2_executive_projection_framework.sh \
    dev/verify_genesis_ui_a3_capability_discovery_registration.sh \
    dev/verify_genesis_ui_a41_knowledge_inventory_projection.sh \
    dev/verify_genesis_vi_a2_executive_mission_control.sh \
    dev/verify_genesis_vi_a3_executive_projection_bus.sh; do
    if [[ -x "$regression" ]]; then
        run_check "Regression: $(basename "$regression")" \
            env PYTHON_BIN="$PYTHON_BIN" "$regression"
    elif [[ -f "$regression" ]]; then
        run_check "Regression: $(basename "$regression")" \
            env PYTHON_BIN="$PYTHON_BIN" bash "$regression"
    else
        echo "[FAIL] Missing regression verifier: $regression"
        FAILURES=$((FAILURES + 1))
    fi
done

printf '%s\n' "------------------------------------------------------------------------" "Checks failed : $FAILURES" "Overall status: $([[ $FAILURES -eq 0 ]] && echo EXCELLENT || echo FAILED)" "========================================================================"
exit "$FAILURES"
