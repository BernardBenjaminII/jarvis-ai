#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "${REPO_ROOT}"
PYTHON_BIN="${PYTHON_BIN:-python}"

PASSED=0
FAILED=0

pass() {
    PASSED=$((PASSED + 1))
    echo "[PASS] $1"
}

fail() {
    FAILED=$((FAILED + 1))
    echo "[FAIL] $1"
}

check() {
    local description="$1"
    shift
    if "$@"; then
        pass "${description}"
    else
        fail "${description}"
    fi
}

echo
echo "======================================================================"
echo "JARVIS GENESIS III-A3 — COGNITIVE WORKSPACE CATALOG & SEARCH"
echo "======================================================================"

check     "Genesis III-A2 prerequisite verification"     env PYTHON_BIN="${PYTHON_BIN}" bash dev/verify_genesis_3a2.sh

check     "Genesis III-A3 package compilation"     "${PYTHON_BIN}" -m compileall -q     core/cognition     dev/verification/verify_genesis_3a3_workspace_catalog_search.py     tests/test_genesis_3a3_workspace_catalog_search.py

check     "Genesis III-A3 structural verification"     "${PYTHON_BIN}"     dev/verification/verify_genesis_3a3_workspace_catalog_search.py

check     "Genesis III-A3 unit tests"     "${PYTHON_BIN}" -m unittest     tests.test_genesis_3a3_workspace_catalog_search

check     "Stable catalog public imports"     "${PYTHON_BIN}" - <<'PY'
from core.cognition import (
    CognitiveWorkspaceCatalog,
    SortDirection,
    WorkspaceCatalogEntry,
    WorkspaceQuery,
    WorkspaceSortField,
)

assert CognitiveWorkspaceCatalog
assert SortDirection
assert WorkspaceCatalogEntry
assert WorkspaceQuery
assert WorkspaceSortField
PY

check     "Deterministic workspace search smoke test"     "${PYTHON_BIN}" - <<'PY'
import tempfile
from pathlib import Path

from core.cognition import (
    CognitiveWorkspaceCatalog,
    CognitiveWorkspaceService,
    Hypothesis,
    SQLiteCognitiveWorkspaceRepository,
    WorkspaceQuery,
)

with tempfile.TemporaryDirectory() as directory:
    repository = SQLiteCognitiveWorkspaceRepository(
        Path(directory) / "workspace.sqlite"
    )
    service = CognitiveWorkspaceService()

    workspace = service.create_workspace(
        "Integrate Meta Quest mission presence",
        workspace_id="cws_meta_quest",
    )
    workspace = service.add_hypothesis(
        workspace,
        Hypothesis.create(
            "Use a progressive spatial interface",
            confidence=0.76,
        ),
    )
    repository.save(workspace)

    catalog = CognitiveWorkspaceCatalog(repository)
    results = catalog.search(
        WorkspaceQuery(text="meta quest spatial")
    )

    assert len(results) == 1
    assert results[0].workspace_id == "cws_meta_quest"
    assert results[0].strongest_confidence == 0.76
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
