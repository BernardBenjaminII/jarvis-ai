#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
export PYTHONPATH="${PROJECT_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"

cd "${PROJECT_ROOT}"

required=(
  "core/governance/constitution/certification/__init__.py"
  "core/governance/constitution/certification/certification.py"
  "core/governance/constitution/certification/executor.py"
  "core/governance/constitution/certification/live_scenarios.py"
  "core/governance/constitution/certification/models.py"
  "core/governance/constitution/certification/reporter.py"
  "tests/test_genesis_vii_c4_1_pack2_live_scenarios.py"
  "dev/verification/verify_genesis_vii_c4_1_pack2_live_scenarios.py"
  "dev/verify_genesis_vii_c4_1_pack2.sh"
  "docs/architecture/governance/constitutional_compliance_live_scenarios.md"
)

for path in "${required[@]}"; do
  test -f "${path}" || { echo "[FAIL] Missing ${path}"; exit 1; }
done
echo "[PASS] Genesis VII-C4.1 Pack 2 canonical file set present"

test -f core/governance/constitution/certification/scenarios.py || {
  echo "[FAIL] Pack 1 is not installed"
  exit 1
}
test -f core/governance/constitution/compliance/engine.py || {
  echo "[FAIL] Genesis VII-C4 is not installed"
  exit 1
}
test -f artifacts/audit/km0000-c4/constitutional_compliance.json || {
  echo "[FAIL] Missing Genesis VII-C4 compliance artifact"
  exit 1
}

"${PYTHON_BIN}" -m py_compile \
  core/governance/constitution/certification/*.py \
  dev/verification/verify_genesis_vii_c4_1_pack2_live_scenarios.py \
  tests/test_genesis_vii_c4_1_pack2_live_scenarios.py
echo "[PASS] Genesis VII-C4.1 Pack 2 Python compilation"

"${PROJECT_ROOT}/dev/verify_genesis_vii_c4_1_pack2.sh"
