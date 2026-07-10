#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/media/abdullah/JARVISDATA/Projects/jarvis-ai"
DB_PATH="/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"

cd "$PROJECT_ROOT"

echo
echo "== Phase IV-D.4: Serialized PDF Repair Tool =="

python -m py_compile \
  dev/stabilization/__init__.py \
  dev/stabilization/repair_serialized_pdf_text.py \
  knowledge_engine/processors/document.py

echo
echo "Compilation passed."

echo
echo "Running repair dry run..."

python -m dev.stabilization.repair_serialized_pdf_text \
  --db "$DB_PATH"

echo
echo "Phase IV-D.4 dry-run verification complete."
