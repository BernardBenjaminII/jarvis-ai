#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
export PYTHONPATH="${PROJECT_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"

cd "${PROJECT_ROOT}"

required=(
  "core/governance/constitution/coverage/graph/directorate_contracts.py"
  "core/governance/constitution/coverage/graph/directorate_models.py"
  "core/governance/constitution/coverage/graph/directorate_builder.py"
  "core/governance/constitution/coverage/graph/directorate_integrity.py"
  "core/governance/constitution/coverage/graph/directorate_foundation.py"
  "core/governance/constitution/coverage/graph/directorate_public_api.py"
  "tests/test_genesis_vii_c4_3_pack3b2b1_directorate_foundation.py"
  "dev/verification/verify_genesis_vii_c4_3_pack3b2b1_directorate_foundation.py"
  "dev/verify_genesis_vii_c4_3_pack3b2b1.sh"
  "docs/architecture/governance/constitutional_directorate_foundation.md"
)

for path in "${required[@]}"; do
  test -f "${path}" || {
    echo "[FAIL] Missing ${path}"
    exit 1
  }
done
echo "[PASS] Genesis VII-C4.3 Pack 3B-2B.1 canonical file set present"

test -f artifacts/audit/km0000-c4_3-pack3b2a/constitutional_repository_projection.json || {
  echo "[FAIL] Missing Pack 3B-2A constitutional repository projection"
  exit 1
}
echo "[PASS] Pack 3B-2A repository projection source present"

"${PYTHON_BIN}" -m py_compile \
  core/governance/constitution/coverage/graph/directorate_*.py \
  tests/test_genesis_vii_c4_3_pack3b2b1_directorate_foundation.py \
  dev/verification/verify_genesis_vii_c4_3_pack3b2b1_directorate_foundation.py
echo "[PASS] Genesis VII-C4.3 Pack 3B-2B.1 Python compilation"

"${PROJECT_ROOT}/dev/verify_genesis_vii_c4_3_pack3b2b1.sh"
