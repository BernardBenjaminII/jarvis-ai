#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="${PROJECT_ROOT:-/media/abdullah/JARVISDATA/Projects/jarvis-ai}"
PYTHON_BIN="${PYTHON_BIN:-/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python}"
cd "$PROJECT_ROOT"
echo "========================================================================"
echo "JARVIS — GENESIS VI-A3A CERTIFICATION REPAIR"
echo "========================================================================"
FAILURES=0
run_check() { local label="$1"; shift; if "$@"; then echo "[PASS] $label"; else echo "[FAIL] $label"; FAILURES=$((FAILURES + 1)); fi; }
run_check "Structural verification" "$PYTHON_BIN" dev/verification/verify_genesis_vi_a3a_certification_repair.py
run_check "Python compilation" "$PYTHON_BIN" -m py_compile core/integration/__init__.py core/integration/bus.py core/integration/readiness.py core/src/routes/operations.py tests/test_genesis_vi_a3a_certification_repair.py
run_check "VI-A3A unit tests" "$PYTHON_BIN" -m unittest tests.test_genesis_vi_a3a_certification_repair
run_check "Integration compatibility" "$PYTHON_BIN" - <<'PYFILE'
import core.integration as integration
from core.integration.contracts import ProjectionEnvelope, ProjectionHealth, ProjectionStatus
assert integration.ExecutiveProjectionBus and ProjectionEnvelope and ProjectionHealth and ProjectionStatus
print("integration exports:", len(integration.__all__))
PYFILE
run_check "Projection Bus smoke test" "$PYTHON_BIN" - <<'PYFILE'
from core.integration import get_default_projection_bus
snapshot = get_default_projection_bus().snapshot().to_dict()
assert snapshot["projections"]
assert snapshot["overall"]["color"] in {"green", "yellow", "red"}
print("projection_ids:", sorted(snapshot["projections"]))
print("overall:", snapshot["overall"]["color"])
print("fingerprint:", snapshot["fingerprint"])
PYFILE
for verifier in dev/verify_genesis_ui_a2_executive_projection_framework.sh dev/verify_genesis_ui_a3_capability_discovery_registration.sh dev/verify_genesis_ui_a41_knowledge_inventory_projection.sh dev/verify_genesis_vi_a2_executive_mission_control.sh dev/verify_genesis_vi_a3_executive_projection_bus.sh; do
    if [[ -x "$verifier" ]]; then run_check "Regression: $(basename "$verifier")" env PYTHON_BIN="$PYTHON_BIN" "$verifier"; fi
done
echo "------------------------------------------------------------------------"
echo "Checks failed : $FAILURES"
if [[ "$FAILURES" -eq 0 ]]; then echo "Overall status: EXCELLENT"; else echo "Overall status: FAILED"; fi
echo "========================================================================"
exit "$FAILURES"
