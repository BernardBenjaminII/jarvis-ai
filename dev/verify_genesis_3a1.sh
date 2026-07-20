#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"

PASSED=0
FAILED=0

pass() { PASSED=$((PASSED + 1)); echo "[PASS] $1"; }
fail() { FAILED=$((FAILED + 1)); echo "[FAIL] $1"; }

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
echo "JARVIS GENESIS III-A1 — COGNITIVE WORKSPACE FOUNDATION"
echo "======================================================================"

check     "Genesis III-A1 package compilation"     "${PYTHON_BIN}" -m compileall -q     core/cognition     dev/verification/verify_genesis_3a1_cognitive_workspace.py     tests/test_genesis_3a1_cognitive_workspace.py

check     "Genesis III-A1 structural verification"     "${PYTHON_BIN}"     dev/verification/verify_genesis_3a1_cognitive_workspace.py

check     "Genesis III-A1 unit tests"     "${PYTHON_BIN}" -m unittest     tests.test_genesis_3a1_cognitive_workspace

check     "Stable cognitive workspace public imports"     "${PYTHON_BIN}" - <<'PY'
from core.cognition import (
    Assumption,
    CognitiveWorkspace,
    CognitiveWorkspaceError,
    CognitiveWorkspaceService,
    EvidenceReference,
    Hypothesis,
    HypothesisStatus,
    OpenQuestion,
    WorkspaceEvent,
    WorkspaceEventKind,
    WorkspaceSnapshot,
    WorkspaceStatus,
)

assert Assumption
assert CognitiveWorkspace
assert CognitiveWorkspaceError
assert CognitiveWorkspaceService
assert EvidenceReference
assert Hypothesis
assert HypothesisStatus
assert OpenQuestion
assert WorkspaceEvent
assert WorkspaceEventKind
assert WorkspaceSnapshot
assert WorkspaceStatus
PY

check     "Deterministic cognitive workspace smoke test"     "${PYTHON_BIN}" - <<'PY'
from core.cognition import (
    CognitiveWorkspaceService,
    EvidenceReference,
    Hypothesis,
    HypothesisStatus,
)

service = CognitiveWorkspaceService()
workspace = service.create_workspace(
    "Select the safest deployment strategy",
    workspace_id="cws_smoke",
)
hypothesis = Hypothesis.create(
    "Use a canary deployment",
    confidence=0.4,
)
workspace = service.add_hypothesis(workspace, hypothesis)
workspace = service.attach_evidence(
    workspace,
    hypothesis.hypothesis_id,
    EvidenceReference(
        evidence_id="ev_smoke",
        summary="Canary deployment limits initial exposure.",
        credibility=0.9,
    ),
)
workspace = service.transition_hypothesis(
    workspace,
    hypothesis.hypothesis_id,
    HypothesisStatus.SUPPORTED,
    confidence=0.82,
    rationale="Evidence supports controlled exposure.",
)

snapshot = workspace.snapshot()

assert snapshot.workspace_id == "cws_smoke"
assert snapshot.hypothesis_count == 1
assert snapshot.evidence_count == 1
assert snapshot.strongest_confidence == 0.82
assert workspace.revision == 3
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
