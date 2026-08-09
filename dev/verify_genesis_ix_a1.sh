#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${PROJECT_ROOT}"
passed=0; failed=0
run_check(){ local label="$1"; shift; if "$@"; then printf '[PASS] %s\n' "$label"; passed=$((passed+1)); else printf '[FAIL] %s\n' "$label"; failed=$((failed+1)); fi; }
echo '========================================================================'
echo 'JARVIS — GENESIS IX-A1'
echo 'KNOWLEDGE WORKSPACE MOUNT'
echo '========================================================================'
run_check "Knowledge Workspace assets" test -s core/src/static/mission_control/knowledge_workspace.js -a -s core/src/static/mission_control/knowledge_workspace.css
run_check "IX-A1 contract tests" "$PYTHON_BIN" -m unittest -v tests.test_genesis_ix_a1_knowledge_workspace_mount
run_check "Conversation API route contracts" "$PYTHON_BIN" - <<'PY'
from core.src.routes.api import router as api_router
from dev.verification.route_contracts import require_routes
contracts = require_routes((api_router,), (("POST","/api/conversation/query"),("POST","/ask")))
for contract in contracts:
    if contract.path in {"/api/conversation/query", "/ask"}:
        print(f"{contract.method} {contract.path}")
PY
run_check "Mission Control asset registration" "$PYTHON_BIN" - <<'PY'
from pathlib import Path
source=Path('core/src/static/mission_control/index.html').read_text(encoding='utf-8')
assert '/mission-control/static/knowledge_workspace.css' in source
assert '/mission-control/static/knowledge_workspace.js' in source
print('OK')
PY
run_check "Architecture document" test -s docs/architecture/genesis_ix_a1_knowledge_workspace_mount.md
echo '------------------------------------------------------------------------'
printf 'Checks passed : %d\n' "$passed"; printf 'Checks failed : %d\n' "$failed"
if [[ $failed -eq 0 ]]; then echo 'Overall status: EXCELLENT'; else echo 'Overall status: FAILED'; fi
echo '========================================================================'
[[ $failed -eq 0 ]]
