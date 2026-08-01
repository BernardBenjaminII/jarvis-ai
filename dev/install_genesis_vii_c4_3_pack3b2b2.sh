#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
export PYTHONPATH="${PROJECT_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"

cd "${PROJECT_ROOT}"

required=(
  "core/governance/constitution/coverage/graph/directorate_assignment.py"
  "core/governance/constitution/coverage/graph/directorate_graph.py"
  "core/governance/constitution/coverage/graph/directorate_metrics.py"
  "core/governance/constitution/coverage/graph/directorate_queries.py"
  "core/governance/constitution/coverage/graph/directorate_projection.py"
  "core/governance/constitution/coverage/graph/directorate_reporting.py"
  "core/governance/constitution/coverage/graph/directorate_projection_public_api.py"
  "tests/test_genesis_vii_c4_3_pack3b2b2_directorate_projection.py"
  "dev/verification/verify_genesis_vii_c4_3_pack3b2b2_directorate_projection.py"
  "dev/verify_genesis_vii_c4_3_pack3b2b2.sh"
  "docs/architecture/governance/constitutional_directorate_projection.md"
)

for path in "${required[@]}"; do
  test -f "${path}" || {
    echo "[FAIL] Missing ${path}"
    exit 1
  }
done
echo "[PASS] Genesis VII-C4.3 Pack 3B-2B.2 canonical file set present"

test -f artifacts/audit/km0000-c4_3-pack3b2b1/constitutional_directorate_foundation.json || {
  echo "[FAIL] Missing Pack 3B-2B.1 directorate foundation artifact"
  exit 1
}
echo "[PASS] Pack 3B-2B.1 directorate foundation source present"

"${PYTHON_BIN}" -m py_compile \
  core/governance/constitution/coverage/graph/directorate_assignment.py \
  core/governance/constitution/coverage/graph/directorate_graph.py \
  core/governance/constitution/coverage/graph/directorate_metrics.py \
  core/governance/constitution/coverage/graph/directorate_queries.py \
  core/governance/constitution/coverage/graph/directorate_projection.py \
  core/governance/constitution/coverage/graph/directorate_reporting.py \
  core/governance/constitution/coverage/graph/directorate_projection_public_api.py \
  tests/test_genesis_vii_c4_3_pack3b2b2_directorate_projection.py \
  dev/verification/verify_genesis_vii_c4_3_pack3b2b2_directorate_projection.py
echo "[PASS] Genesis VII-C4.3 Pack 3B-2B.2 Python compilation"

"${PROJECT_ROOT}/dev/verify_genesis_vii_c4_3_pack3b2b2.sh"
