#!/usr/bin/env bash
set -euo pipefail

cd /media/abdullah/JARVISDATA/Projects/jarvis-ai

FIXTURE="dev/integration/fixtures/phase_ii_c_sample.txt"

echo
echo "== Phase IV-A: Knowledge Director Foundation =="

python -m py_compile \
  knowledge_engine/director/models.py \
  knowledge_engine/director/knowledge_director.py \
  knowledge_engine/director_cli.py \
  dev/doctor/director.py

python -m knowledge_engine.director_cli ingest_fixture --source "$FIXTURE"
python -m dev.doctor.doctor

echo
echo "Phase IV-A verification complete."
