#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_ROOT"
PYTHON_BIN="${PYTHON_BIN:-python}"

echo
echo "======================================================================"
echo "JARVIS GEN 2 — GENESIS I-A2 REASONING SERVICE AUDIT"
echo "======================================================================"

checks_failed=0
run_check() {
    local title="$1"
    shift
    if "$@"; then
        echo "[PASS] $title"
    else
        echo "[FAIL] $title"
        checks_failed=$((checks_failed + 1))
    fi
}

run_check "Audit tool compilation" "$PYTHON_BIN" -m py_compile dev/tools/audit_reasoning_services.py
run_check "Deterministic report check" "$PYTHON_BIN" dev/tools/audit_reasoning_services.py --check
run_check "JSON certification structure" "$PYTHON_BIN" -c '
import json
from pathlib import Path
p = Path("docs/architecture/convergence/genesis_1a2_reasoning_service_audit.json")
r = json.loads(p.read_text(encoding="utf-8"))
assert r["audit_id"] == "GENESIS-I-A2"
assert r["status"] == "PASS"
assert r["audit_fingerprint"]
assert r["summary"]["checks_failed"] == 0
assert any(s["name"] == "ReasoningEngine" for s in r["services"])
'
run_check "Markdown report exists" test -s docs/architecture/convergence/genesis_1a2_reasoning_service_audit.md

echo "----------------------------------------------------------------------"
echo "Checks failed : $checks_failed"
if [[ "$checks_failed" -ne 0 ]]; then
    echo "Overall status: FAILED"
    echo "======================================================================"
    exit 1
fi
echo "Overall status: EXCELLENT"
echo "======================================================================"
