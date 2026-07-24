#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

cd "$ROOT"

echo "======================================================================"
echo "JARVIS GENESIS III-A3A — COGNITIVE WORKSPACE PUBLIC SURFACE RESTORATION"
echo "======================================================================"

"$PYTHON_BIN" dev/verification/verify_genesis_3a3a.py

"$PYTHON_BIN" -m py_compile \
    core/cognition/__init__.py \
    tests/test_genesis_3a3a_cognitive_workspace_public_surface.py

echo "[PASS] Genesis III-A3A package compilation"

"$PYTHON_BIN" -m unittest \
    tests.test_genesis_3a3a_cognitive_workspace_public_surface

echo "[PASS] Genesis III-A3A deterministic unit tests"

"$PYTHON_BIN" - <<'PY'
from core.cognition import (
    Assumption,
    CognitiveWorkspaceCatalog,
    CognitiveWorkspaceCodec,
    CognitiveWorkspaceService,
)
from core.cognition.workspace import (
    Assumption as WorkspaceAssumption,
    CognitiveWorkspaceCatalog as WorkspaceCatalog,
    CognitiveWorkspaceCodec as WorkspaceCodec,
    CognitiveWorkspaceService as WorkspaceService,
)

assert Assumption is WorkspaceAssumption
assert CognitiveWorkspaceCatalog is WorkspaceCatalog
assert CognitiveWorkspaceCodec is WorkspaceCodec
assert CognitiveWorkspaceService is WorkspaceService
print("[PASS] Stable cognitive workspace root imports")
PY

echo "----------------------------------------------------------------------"
echo "Checks failed : 0"
echo "Overall status: EXCELLENT"
echo "======================================================================"
