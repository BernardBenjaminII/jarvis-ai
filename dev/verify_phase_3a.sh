#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/media/abdullah/JARVISDATA/Projects/jarvis-ai"
FIXTURE="dev/integration/fixtures/phase_ii_c_sample.txt"

cd "$PROJECT_ROOT"

echo
echo "== Phase 3A: Knowledge Workflow Framework =="

python -m py_compile \
  knowledge_engine/workflows/core/context.py \
  knowledge_engine/workflows/core/stage.py \
  knowledge_engine/workflows/core/report.py \
  knowledge_engine/workflows/core/runner.py \
  knowledge_engine/workflows/core/simple_stages.py \
  knowledge_engine/workflows/fixture_ingest.py \
  knowledge_engine/fixture_workflow_cli.py \
  dev/doctor/workflow.py

python -m knowledge_engine.fixture_workflow_cli "$FIXTURE"
python -m dev.doctor.doctor

echo
echo "Phase 3A verification complete."
