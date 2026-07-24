#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$ROOT"

echo "========================================================================"
echo "JARVIS — GENESIS UI-A4.1 KNOWLEDGE INVENTORY PROJECTION"
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
    "$PYTHON_BIN" \
    dev/verification/verify_genesis_ui_a41_knowledge_inventory_projection.py

run_check \
    "Python compilation" \
    "$PYTHON_BIN" -m py_compile \
        core/integration/knowledge_inventory.py \
        core/integration/providers/knowledge.py \
        core/integration/providers/__init__.py \
        core/integration/bootstrap.py \
        tests/test_genesis_ui_a41_knowledge_inventory_projection.py

run_check \
    "UI-A4.1 unit tests" \
    "$PYTHON_BIN" -m unittest \
        tests.test_genesis_ui_a41_knowledge_inventory_projection

run_check \
    "Knowledge projection import smoke test" \
    "$PYTHON_BIN" -c \
        "from core.integration.providers.knowledge import KnowledgeProjectionProvider; from core.integration.knowledge_inventory import KnowledgeInventoryService; assert KnowledgeProjectionProvider.projection_id == 'knowledge'; assert KnowledgeInventoryService"

run_check \
    "Default bootstrap projection registration" \
    "$PYTHON_BIN" -c \
        "from core.integration.bootstrap import build_default_integration_runtime; r=build_default_integration_runtime(capability_packages=[]); assert 'operations' in r.projection_registry; assert 'capabilities' in r.projection_registry; assert 'knowledge' in r.projection_registry"

if [[ -x ./dev/verify_genesis_ui_a3_capability_discovery_registration.sh ]]; then
    run_check \
        "Genesis UI-A3 regression" \
        env PYTHON_BIN="$PYTHON_BIN" \
        ./dev/verify_genesis_ui_a3_capability_discovery_registration.sh
else
    echo "[SKIP] Genesis UI-A3 verifier not present"
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
