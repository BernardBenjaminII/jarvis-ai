#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${PROJECT_ROOT}"
passed=0; failed=0
run_check(){ local label="$1"; shift; if "$@"; then printf '[PASS] %s\n' "$label"; passed=$((passed+1)); else printf '[FAIL] %s\n' "$label"; failed=$((failed+1)); fi; }
echo '========================================================================'
echo 'JARVIS — GENESIS IX-A1.1'
echo 'CANONICAL ROUTE VERIFICATION'
echo '========================================================================'
run_check "Route verification helper compilation" "$PYTHON_BIN" -m py_compile dev/verification/route_contracts.py
run_check "Canonical route verification tests" "$PYTHON_BIN" -m unittest -v tests.test_genesis_ix_a1_1_canonical_route_verification
run_check "Canonical Conversation API contracts" "$PYTHON_BIN" - <<'PY'
from core.src.routes.api import router as api_router
from dev.verification.route_contracts import require_routes
require_routes((api_router,), (
    ("POST","/ask"),
    ("POST","/api/conversation/query"),
    ("GET","/api/conversation/sessions/{session_id}"),
    ("GET","/api/conversation/sessions/{session_id}/messages"),
))
print('OK')
PY
run_check "IX-A1 regression" env PYTHON_BIN="$PYTHON_BIN" ./dev/verify_genesis_ix_a1.sh
run_check "Architecture document exists" test -s docs/architecture/genesis_ix_a1_1_canonical_route_verification.md
echo '------------------------------------------------------------------------'
printf 'Checks passed : %d\n' "$passed"; printf 'Checks failed : %d\n' "$failed"
if [[ $failed -eq 0 ]]; then echo 'Overall status: EXCELLENT'; else echo 'Overall status: FAILED'; fi
echo '========================================================================'
[[ $failed -eq 0 ]]
