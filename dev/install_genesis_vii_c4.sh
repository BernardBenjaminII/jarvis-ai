#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
export PYTHONPATH="${PROJECT_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"

cd "${PROJECT_ROOT}"

required=(
  "core/governance/constitution/compliance/__init__.py"
  "core/governance/constitution/compliance/contracts.py"
  "core/governance/constitution/compliance/models.py"
  "core/governance/constitution/compliance/normalize.py"
  "core/governance/constitution/compliance/loader.py"
  "core/governance/constitution/compliance/evaluator.py"
  "core/governance/constitution/compliance/engine.py"
  "core/governance/constitution/compliance/reporting.py"
  "tests/test_genesis_vii_c4_constitutional_compliance.py"
  "dev/verification/verify_genesis_vii_c4_constitutional_compliance.py"
  "dev/verify_genesis_vii_c4.sh"
  "docs/architecture/governance/constitutional_compliance_engine.md"
)

for path in "${required[@]}"; do
  test -f "${path}" || { echo "[FAIL] Missing ${path}"; exit 1; }
done
echo "[PASS] Genesis VII-C4 canonical file set present"

test -f artifacts/audit/km0000-c3/constitutional_ratification.json || {
  echo "[FAIL] Missing C3 constitutional_ratification.json"
  exit 1
}

test -f artifacts/audit/km0000-c3/constitutional_registry.json || {
  echo "[FAIL] Missing C3 constitutional_registry.json"
  exit 1
}

"${PYTHON_BIN}" -m py_compile \
  core/governance/constitution/compliance/*.py \
  dev/verification/verify_genesis_vii_c4_constitutional_compliance.py \
  tests/test_genesis_vii_c4_constitutional_compliance.py
echo "[PASS] Genesis VII-C4 Python compilation"

"${PROJECT_ROOT}/dev/verify_genesis_vii_c4.sh"
