#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
cd "$PROJECT_ROOT"

required=(
  core/governance/constitution/__init__.py
  core/governance/constitution/extraction/__init__.py
  core/governance/constitution/extraction/contracts.py
  core/governance/constitution/extraction/models.py
  core/governance/constitution/extraction/rules.py
  core/governance/constitution/extraction/markdown.py
  core/governance/constitution/extraction/engine.py
  tests/test_genesis_vii_c1_constitutional_extraction.py
  dev/verification/verify_genesis_vii_c1_constitutional_extraction.py
  dev/verify_genesis_vii_c1.sh
  docs/architecture/governance/constitutional_extraction_engine.md
)
for path in "${required[@]}"; do
  [[ -f "$path" ]] || { echo "[FAIL] Missing $path"; exit 1; }
done

echo "[PASS] Genesis VII-C1 canonical file set present"
mkdir -p artifacts/audit/km0000-c1

"$PYTHON_BIN" -m py_compile   core/governance/constitution/__init__.py   core/governance/constitution/extraction/*.py   dev/verification/verify_genesis_vii_c1_constitutional_extraction.py   tests/test_genesis_vii_c1_constitutional_extraction.py

echo "[PASS] Genesis VII-C1 Python compilation"
PYTHON_BIN="$PYTHON_BIN" ./dev/verify_genesis_vii_c1.sh
