#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/media/abdullah/JARVISDATA/Projects/jarvis-ai"
VENV_PY="/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python"

cd "$PROJECT_ROOT"

echo
echo "== Architecture Blueprint Verification =="

"$VENV_PY" -m py_compile \
  dev/consolidation/governance/verify_architecture_blueprint.py

"$VENV_PY" -m dev.consolidation.governance.verify_architecture_blueprint

echo
echo "Architecture blueprint verification complete."
