#!/usr/bin/env bash
set -euo pipefail

cd /media/abdullah/JARVISDATA/Projects/jarvis-ai

FIXTURE="dev/integration/fixtures/phase_ii_c_sample.txt"

echo
echo "== Phase III-D: Service Consolidation =="

python -m py_compile \
  knowledge_engine/workflows/core/context.py \
  knowledge_engine/workflows/stages/extraction.py \
  knowledge_engine/workflows/stages/chunking.py \
  knowledge_engine/workflows/stages/embeddings.py \
  knowledge_engine/workflows/stages/registry.py \
  knowledge_engine/workflows/stages/retrieval.py \
  knowledge_engine/fixture_workflow_cli.py \
  dev/doctor/services.py

python -m knowledge_engine.fixture_workflow_cli "$FIXTURE"
python -m dev.doctor.doctor

echo
echo "Phase III-D verification complete."
