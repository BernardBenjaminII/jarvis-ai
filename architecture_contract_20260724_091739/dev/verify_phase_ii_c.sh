#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/media/abdullah/JARVISDATA/Projects/jarvis-ai"

cd "$PROJECT_ROOT"

echo
echo "== Phase II-C: Knowledge Engine Integration =="

python -m py_compile dev/integration/knowledge_pipeline_check.py
python -m dev.integration.knowledge_pipeline_check

echo
echo "Phase II-C verification complete."
