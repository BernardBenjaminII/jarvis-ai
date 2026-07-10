#!/usr/bin/env bash
set -euo pipefail

cd /media/abdullah/JARVISDATA/Projects/jarvis-ai

FIXTURE="dev/integration/fixtures/phase_ii_c_sample.txt"

echo
echo "== Phase IV-B: Workflow Registry =="

python -m py_compile \
  knowledge_engine/director/workflow.py \
  knowledge_engine/director/workflow_registry.py \
  knowledge_engine/director/workflows/*.py \
  knowledge_engine/director/knowledge_director.py

python -m knowledge_engine.director_cli \
  ingest_fixture \
  --source "$FIXTURE"

python -m dev.doctor.doctor

echo
echo "Phase IV-B verification complete."
