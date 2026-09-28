#!/usr/bin/env bash
set -euo pipefail

cd /media/abdullah/JARVISDATA/Projects/jarvis-ai

echo
echo "== Phase IV-C: Search Workflow =="

python -m py_compile \
  knowledge_engine/director/workflows/search.py \
  knowledge_engine/director_cli.py \
  dev/doctor/search.py

python - <<'PY'
from knowledge_engine.director.knowledge_director import KnowledgeDirector

director = KnowledgeDirector()
required = {"ingest_fixture", "search"}
intents = set(director.registry.intents())
missing = required - intents

if missing:
    raise SystemExit(f"Missing workflows: {sorted(missing)}")

print("Registered workflows:", sorted(intents))
PY

python -m knowledge_engine.director_cli \
  search \
  --query "JARVIS integration sample" \
  --limit 3

python -m dev.doctor.doctor

echo
echo "Phase IV-C verification complete."
