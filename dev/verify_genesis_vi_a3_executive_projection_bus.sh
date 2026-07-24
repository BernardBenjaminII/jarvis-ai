#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/media/abdullah/JARVISDATA/Projects/jarvis-ai}"
PYTHON_BIN="${PYTHON_BIN:-/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python}"
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

echo "========================================================================"
echo "JARVIS — GENESIS VI-A3 EXECUTIVE PROJECTION BUS"
echo "========================================================================"

run_check "Structural verification" \
    "$PYTHON_BIN" dev/verification/verify_genesis_vi_a3_executive_projection_bus.py

run_check "Python compilation" \
    "$PYTHON_BIN" -m py_compile \
        core/integration/readiness.py \
        core/integration/bus.py \
        core/integration/__init__.py \
        core/src/routes/operations.py \
        tests/test_genesis_vi_a3_executive_projection_bus.py

run_check "VI-A3 unit tests" \
    "$PYTHON_BIN" -m unittest tests.test_genesis_vi_a3_executive_projection_bus

run_check "Canonical runtime smoke test" \
    "$PYTHON_BIN" - <<'PY'
from core.integration import get_default_projection_bus
snapshot = get_default_projection_bus().snapshot().to_dict()
assert snapshot["schema_version"] == "1.0"
assert snapshot["revision"] >= 1
assert {"capabilities", "knowledge", "operations"}.issubset(snapshot["projections"])
assert snapshot["overall"]["color"] in {"green", "yellow", "red"}
print("projection_ids:", sorted(snapshot["projections"]))
print("overall:", snapshot["overall"]["color"])
print("revision:", snapshot["revision"])
print("fingerprint:", snapshot["fingerprint"])
PY

if [[ -x dev/verify_genesis_vi_a2_executive_mission_control.sh ]]; then
    run_check "Genesis VI-A2 regression" \
        env PYTHON_BIN="$PYTHON_BIN" ./dev/verify_genesis_vi_a2_executive_mission_control.sh
fi

if [[ -x dev/verify_genesis_ui_a41_knowledge_inventory_projection.sh ]]; then
    run_check "Genesis UI-A4.1 regression" \
        env PYTHON_BIN="$PYTHON_BIN" ./dev/verify_genesis_ui_a41_knowledge_inventory_projection.sh
fi

echo "------------------------------------------------------------------------"
echo "Checks failed : $FAILURES"
echo "Overall status: $([[ $FAILURES -eq 0 ]] && echo EXCELLENT || echo FAILED)"
echo "========================================================================"
exit "$FAILURES"
