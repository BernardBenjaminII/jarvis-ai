#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$ROOT"

echo "========================================================================"
echo "JARVIS — GENESIS UI-A3 CAPABILITY DISCOVERY & REGISTRATION"
echo "========================================================================"

failures=0

run_check() {
    local label="$1"
    shift

    if "$@"; then
        echo "[PASS] $label"
    else
        echo "[FAIL] $label"
        failures=$((failures + 1))
    fi
}

run_check \
    "Structural verification" \
    "$PYTHON_BIN" dev/verification/verify_genesis_ui_a3_capability_discovery_registration.py

run_check \
    "Python compilation" \
    "$PYTHON_BIN" -m py_compile \
        core/capabilities/__init__.py \
        core/capabilities/discovery.py \
        core/capabilities/metadata.py \
        core/capabilities/operations.py \
        core/integration/bootstrap.py \
        core/integration/providers/capabilities.py \
        core/integration/providers/operations.py \
        tests/test_genesis_ui_a3_capability_discovery_registration.py

run_check \
    "UI-A3 unit tests" \
    "$PYTHON_BIN" -m unittest \
        tests.test_genesis_ui_a3_capability_discovery_registration

run_check \
    "Capability registry smoke test" \
    "$PYTHON_BIN" -c \
        "from core.integration.bootstrap import build_default_integration_runtime; r=build_default_integration_runtime(capability_packages=[]); names={c.name for c in r.capability_registry.all()}; assert len(names)>=7; assert 'operations.status' in names; assert 'operations.events' in names"

run_check \
    "Capability projection smoke test" \
    "$PYTHON_BIN" -c \
        "from core.integration.bootstrap import build_default_integration_runtime; r=build_default_integration_runtime(capability_packages=[]); p=r.projection_service.projection('capabilities').to_dict(); assert p['health']['status']=='available'; assert p['data']['bound']>=7"

if [[ -x ./dev/verify_genesis_ui_a2_executive_projection_framework.sh ]]; then
    run_check \
        "Genesis UI-A2 regression" \
        env PYTHON_BIN="$PYTHON_BIN" \
        ./dev/verify_genesis_ui_a2_executive_projection_framework.sh
else
    echo "[SKIP] Genesis UI-A2 verifier not present"
fi

if [[ -x ./dev/verify_executive_integration_pack.sh ]]; then
    run_check \
        "Genesis UI-A1 regression" \
        env PYTHON_BIN="$PYTHON_BIN" \
        ./dev/verify_executive_integration_pack.sh
else
    echo "[SKIP] Genesis UI-A1 verifier not present"
fi

echo "------------------------------------------------------------------------"
echo "Checks failed : $failures"

if [[ "$failures" -eq 0 ]]; then
    echo "Overall status: EXCELLENT"
    echo "========================================================================"
    exit 0
fi

echo "Overall status: FAILED"
echo "========================================================================"
exit 1
