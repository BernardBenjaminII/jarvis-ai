#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
export PYTHONPATH="${PROJECT_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"

cd "${PROJECT_ROOT}"

required=(
  "core/governance/constitution/coverage/graph/authority_contracts.py"
  "core/governance/constitution/coverage/graph/authority_models.py"
  "core/governance/constitution/coverage/graph/authority_builder.py"
  "core/governance/constitution/coverage/graph/authority_integrity.py"
  "core/governance/constitution/coverage/graph/authority_metrics.py"
  "core/governance/constitution/coverage/graph/authority_graph.py"
  "core/governance/constitution/coverage/graph/authority_engine.py"
  "core/governance/constitution/coverage/graph/authority_reporting.py"
  "core/governance/constitution/coverage/graph/authority_queries.py"
  "core/governance/constitution/coverage/graph/authority_public_api.py"
  "tests/test_genesis_vii_c4_3_pack3b1_constitutional_authority_graph.py"
  "dev/verification/verify_genesis_vii_c4_3_pack3b1_constitutional_authority_graph.py"
  "dev/verify_genesis_vii_c4_3_pack3b1.sh"
  "docs/architecture/governance/constitutional_authority_graph.md"
)

for path in "${required[@]}"; do
  test -f "${path}" || {
    echo "[FAIL] Missing ${path}"
    exit 1
  }
done
echo "[PASS] Genesis VII-C4.3 Pack 3B-1 canonical file set present"

test -f artifacts/audit/km0000-c4_3-pack3a/constitutional_graph_foundation.json || {
  echo "[FAIL] Missing Pack 3A constitutional graph foundation artifact"
  exit 1
}
echo "[PASS] Pack 3A graph foundation source present"

"${PYTHON_BIN}" -m py_compile \
  core/governance/constitution/coverage/graph/authority_*.py \
  tests/test_genesis_vii_c4_3_pack3b1_constitutional_authority_graph.py \
  dev/verification/verify_genesis_vii_c4_3_pack3b1_constitutional_authority_graph.py
echo "[PASS] Genesis VII-C4.3 Pack 3B-1 Python compilation"

"${PROJECT_ROOT}/dev/verify_genesis_vii_c4_3_pack3b1.sh"
