#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
export PYTHONPATH="${PROJECT_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"

cd "${PROJECT_ROOT}"

required=(
  "core/governance/constitution/analysis/__init__.py"
  "core/governance/constitution/analysis/contracts.py"
  "core/governance/constitution/analysis/models.py"
  "core/governance/constitution/analysis/normalize.py"
  "core/governance/constitution/analysis/authority.py"
  "core/governance/constitution/analysis/loader.py"
  "core/governance/constitution/analysis/detectors.py"
  "core/governance/constitution/analysis/engine.py"
  "core/governance/constitution/analysis/reporting.py"
  "tests/test_genesis_vii_c2_constitutional_analysis.py"
  "dev/verification/verify_genesis_vii_c2_constitutional_analysis.py"
  "dev/verify_genesis_vii_c2.sh"
  "docs/architecture/governance/constitutional_analysis_engine.md"
)

for path in "${required[@]}"; do
  test -f "${path}" || { echo "[FAIL] Missing ${path}"; exit 1; }
done
echo "[PASS] Genesis VII-C2 canonical file set present"

"${PYTHON_BIN}" -m py_compile \
  core/governance/constitution/analysis/*.py \
  dev/verification/verify_genesis_vii_c2_constitutional_analysis.py \
  tests/test_genesis_vii_c2_constitutional_analysis.py
echo "[PASS] Genesis VII-C2 Python compilation"

"${PROJECT_ROOT}/dev/verify_genesis_vii_c2.sh"
