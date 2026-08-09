#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${PROJECT_ROOT}"
passed=0; failed=0
run_check() {
    local label="$1"; shift
    if "$@"; then echo "[PASS] ${label}"; passed=$((passed+1))
    else echo "[FAIL] ${label}"; failed=$((failed+1)); fi
}
echo "========================================================================"
echo "JARVIS — GENESIS IX-A2"
echo "CONVERSATION INTEGRATION"
echo "========================================================================"
run_check "IX-A2 package compilation" \
  "${PYTHON_BIN}" -m py_compile \
  core/executive/conversation/contracts.py \
  core/executive/conversation/adapter.py \
  core/src/routes/knowledge_workspace.py \
  tests/test_genesis_ix_a2_conversation_integration.py
run_check "IX-A2 integration tests" \
  "${PYTHON_BIN}" -m unittest -v tests.test_genesis_ix_a2_conversation_integration
run_check "Canonical workspace route" \
  "${PYTHON_BIN}" - <<'PY'
from core.src.routes.knowledge_workspace import router
contracts={(m,r.path) for r in router.routes for m in getattr(r,"methods",())}
assert ("POST","/api/knowledge/conversation") in contracts
print("POST /api/knowledge/conversation")
PY
run_check "Workspace client integration" \
  grep -q '"/api/knowledge/conversation"' \
  core/src/static/mission_control/knowledge_workspace.js
run_check "IX-A1 regression" \
  env PYTHON_BIN="${PYTHON_BIN}" ./dev/verify_genesis_ix_a1.sh
run_check "Architecture document" \
  test -s docs/architecture/genesis_ix_a2_conversation_integration.md
echo "------------------------------------------------------------------------"
echo "Checks passed : ${passed}"
echo "Checks failed : ${failed}"
[[ ${failed} -eq 0 ]] && echo "Overall status: EXCELLENT" || echo "Overall status: FAILED"
echo "========================================================================"
[[ ${failed} -eq 0 ]]
