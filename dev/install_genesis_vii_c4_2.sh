#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
export PYTHONPATH="${PROJECT_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"

cd "${PROJECT_ROOT}"

required=(
  "core/governance/constitution/repository_audit/__init__.py"
  "core/governance/constitution/repository_audit/contracts.py"
  "core/governance/constitution/repository_audit/models.py"
  "core/governance/constitution/repository_audit/fingerprints.py"
  "core/governance/constitution/repository_audit/policies.py"
  "core/governance/constitution/repository_audit/discovery.py"
  "core/governance/constitution/repository_audit/evaluator.py"
  "core/governance/constitution/repository_audit/statistics.py"
  "core/governance/constitution/repository_audit/engine.py"
  "core/governance/constitution/repository_audit/reporting.py"
  "tests/test_genesis_vii_c4_2_repository_constitutional_audit.py"
  "dev/verification/verify_genesis_vii_c4_2_repository_constitutional_audit.py"
  "dev/verify_genesis_vii_c4_2.sh"
  "docs/architecture/governance/repository_wide_constitutional_audit.md"
)

for path in "${required[@]}"; do
  test -f "${path}" || { echo "[FAIL] Missing ${path}"; exit 1; }
done
echo "[PASS] Genesis VII-C4.2 canonical file set present"

test -f core/governance/constitution/compliance/engine.py || {
  echo "[FAIL] Genesis VII-C4 is not installed"
  exit 1
}
test -f artifacts/audit/km0000-c4/constitutional_compliance.json || {
  echo "[FAIL] Missing Genesis VII-C4 compliance artifact"
  exit 1
}
test -f artifacts/audit/km0000-c4_1-pack2/constitutional_certification.json || {
  echo "[FAIL] Missing Genesis VII-C4.1 Pack 2 certification artifact"
  exit 1
}

"${PYTHON_BIN}" -m py_compile \
  core/governance/constitution/repository_audit/*.py \
  dev/verification/verify_genesis_vii_c4_2_repository_constitutional_audit.py \
  tests/test_genesis_vii_c4_2_repository_constitutional_audit.py
echo "[PASS] Genesis VII-C4.2 Python compilation"

"${PROJECT_ROOT}/dev/verify_genesis_vii_c4_2.sh"
