#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "$ROOT"

echo "======================================================================"
echo "JARVIS GENESIS III-A4 — COGNITIVE WORKSPACE INTEGRATION ENGINE"
echo "======================================================================"

"$PYTHON_BIN" -m py_compile core/cognition/integration/*.py tests/test_genesis_3a4_cognitive_workspace_integration.py
printf '[PASS] Genesis III-A4 package compilation\n'
"$PYTHON_BIN" dev/verification/verify_genesis_3a4.py
"$PYTHON_BIN" -m unittest -v tests.test_genesis_3a4_cognitive_workspace_integration
printf '[PASS] Genesis III-A4 unit tests\n'
"$PYTHON_BIN" - <<'PY'
from core.cognition.integration import (
    CognitiveWorkspaceIntegrationDirector,
    CognitiveWorkspaceIntegrationService,
    WorkspaceIntegrationPipeline,
    WorkspaceIntegrationRequest,
)
assert WorkspaceIntegrationRequest
assert WorkspaceIntegrationPipeline
assert CognitiveWorkspaceIntegrationService
assert CognitiveWorkspaceIntegrationDirector
print('[PASS] Stable Genesis III-A4 public imports')
PY

if [[ -x dev/verify_genesis_3a3.sh ]]; then
  PYTHON_BIN="$PYTHON_BIN" ./dev/verify_genesis_3a3.sh >/dev/null
  printf '[PASS] Genesis III-A3 regression\n'
fi

echo "----------------------------------------------------------------------"
echo "Checks failed : 0"
echo "Overall status: EXCELLENT"
echo "======================================================================"
