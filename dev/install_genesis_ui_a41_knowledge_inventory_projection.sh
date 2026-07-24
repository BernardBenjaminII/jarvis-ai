#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$ROOT"

echo "========================================================================"
echo "INSTALLING JARVIS — GENESIS UI-A4.1 KNOWLEDGE INVENTORY PROJECTION"
echo "========================================================================"

required=(
  "core/integration/knowledge_inventory.py"
  "core/integration/providers/knowledge.py"
  "core/integration/providers/__init__.py"
  "core/integration/bootstrap.py"
  "tests/test_genesis_ui_a41_knowledge_inventory_projection.py"
  "dev/verification/verify_genesis_ui_a41_knowledge_inventory_projection.py"
  "dev/verify_genesis_ui_a41_knowledge_inventory_projection.sh"
)

for file in "${required[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "[FAIL] Missing pack file: $file"
    exit 1
  fi
done

chmod +x \
  dev/verification/verify_genesis_ui_a41_knowledge_inventory_projection.py \
  dev/verify_genesis_ui_a41_knowledge_inventory_projection.sh

PYTHON_BIN="$PYTHON_BIN" \
./dev/verify_genesis_ui_a41_knowledge_inventory_projection.sh

echo
echo "[PASS] Genesis UI-A4.1 Knowledge Inventory Projection installed"
echo "[NOTE] Restart the JARVIS API before runtime verification."
