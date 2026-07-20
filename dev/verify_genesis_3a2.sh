#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "${REPO_ROOT}"
PYTHON_BIN="${PYTHON_BIN:-python}"

PASSED=0
FAILED=0
pass(){ PASSED=$((PASSED+1)); echo "[PASS] $1"; }
fail(){ FAILED=$((FAILED+1)); echo "[FAIL] $1"; }
check(){ local d="$1"; shift; if "$@"; then pass "$d"; else fail "$d"; fi; }

echo
echo "======================================================================"
echo "JARVIS GENESIS III-A2 — PERSISTENT COGNITIVE WORKSPACE REPOSITORY"
echo "======================================================================"

check "Genesis III-A1 prerequisite verification"   env PYTHON_BIN="${PYTHON_BIN}" bash dev/verify_genesis_3a1.sh

check "Genesis III-A2 package compilation"   "${PYTHON_BIN}" -m compileall -q   core/cognition   dev/verification/verify_genesis_3a2_persistent_workspace_repository.py   tests/test_genesis_3a2_persistent_workspace_repository.py

check "Genesis III-A2 structural verification"   "${PYTHON_BIN}"   dev/verification/verify_genesis_3a2_persistent_workspace_repository.py

check "Genesis III-A2 unit tests"   "${PYTHON_BIN}" -m unittest   tests.test_genesis_3a2_persistent_workspace_repository

check "Stable repository public imports" "${PYTHON_BIN}" - <<'PY'
from core.cognition import (
    CognitiveWorkspaceCodec,
    CognitiveWorkspaceConflictError,
    CognitiveWorkspaceNotFoundError,
    CognitiveWorkspaceRepository,
    CognitiveWorkspaceRepositoryError,
    SQLiteCognitiveWorkspaceRepository,
)

assert CognitiveWorkspaceCodec
assert CognitiveWorkspaceConflictError
assert CognitiveWorkspaceNotFoundError
assert CognitiveWorkspaceRepository
assert CognitiveWorkspaceRepositoryError
assert SQLiteCognitiveWorkspaceRepository
PY

check "Persistent repository smoke test" "${PYTHON_BIN}" - <<'PY'
import tempfile
from pathlib import Path

from core.cognition import (
    CognitiveWorkspaceService,
    Hypothesis,
    SQLiteCognitiveWorkspaceRepository,
)

with tempfile.TemporaryDirectory() as directory:
    repository = SQLiteCognitiveWorkspaceRepository(
        Path(directory) / "workspace.sqlite"
    )
    service = CognitiveWorkspaceService()
    workspace = service.create_workspace(
        "Select a resilient deployment strategy",
        workspace_id="cws_smoke_persistent",
    )
    repository.save(workspace)
    workspace = service.add_hypothesis(
        workspace,
        Hypothesis.create("Use blue-green deployment"),
    )
    repository.save(workspace, expected_revision=0)
    restored = repository.get(workspace.workspace_id)

    assert restored == workspace
    assert restored.revision == 1
    assert repository.list_ids() == ("cws_smoke_persistent",)
PY

echo "----------------------------------------------------------------------"
echo "Checks passed : ${PASSED}"
echo "Checks failed : ${FAILED}"
if [[ "${FAILED}" -eq 0 ]]; then
    echo "Overall status: EXCELLENT"
    echo "======================================================================"
    exit 0
fi
echo "Overall status: FAILED"
echo "======================================================================"
exit 1
