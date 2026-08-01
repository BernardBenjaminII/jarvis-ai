#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
export PYTHONPATH="${PROJECT_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"

cd "${PROJECT_ROOT}"

required=(
  "core/governance/constitution/certification/__init__.py"
  "core/governance/constitution/certification/contracts.py"
  "core/governance/constitution/certification/models.py"
  "core/governance/constitution/certification/identifiers.py"
  "core/governance/constitution/certification/policies.py"
  "core/governance/constitution/certification/fingerprints.py"
  "core/governance/constitution/certification/scenarios.py"
  "core/governance/constitution/certification/certification.py"
  "core/governance/constitution/certification/reporter.py"
  "tests/test_genesis_vii_c4_1_pack1_certification_framework.py"
  "dev/verification/verify_genesis_vii_c4_1_pack1_certification_framework.py"
  "dev/verify_genesis_vii_c4_1_pack1.sh"
  "docs/architecture/governance/constitutional_compliance_certification_framework.md"
)

for path in "${required[@]}"; do
  test -f "${path}" || { echo "[FAIL] Missing ${path}"; exit 1; }
done
echo "[PASS] Genesis VII-C4.1 Pack 1 canonical file set present"

test -f artifacts/audit/km0000-c4/constitutional_compliance.json || {
  echo "[FAIL] Missing C4 constitutional_compliance.json"
  exit 1
}

"${PYTHON_BIN}" -m py_compile \
  core/governance/constitution/certification/*.py \
  dev/verification/verify_genesis_vii_c4_1_pack1_certification_framework.py \
  tests/test_genesis_vii_c4_1_pack1_certification_framework.py
echo "[PASS] Genesis VII-C4.1 Pack 1 Python compilation"

"${PROJECT_ROOT}/dev/verify_genesis_vii_c4_1_pack1.sh"
