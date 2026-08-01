#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
export PYTHONPATH="${PROJECT_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"

cd "${PROJECT_ROOT}"

required=(
  "core/governance/constitution/coverage/graph/__init__.py"
  "core/governance/constitution/coverage/graph/contracts.py"
  "core/governance/constitution/coverage/graph/models.py"
  "core/governance/constitution/coverage/graph/graph.py"
  "core/governance/constitution/coverage/graph/builder.py"
  "core/governance/constitution/coverage/graph/integrity.py"
  "core/governance/constitution/coverage/graph/metrics.py"
  "core/governance/constitution/coverage/graph/serialization.py"
  "core/governance/constitution/coverage/graph/engine.py"
  "core/governance/constitution/coverage/graph/reporting.py"
  "tests/test_genesis_vii_c4_3_pack3a_constitutional_graph_foundation.py"
  "dev/verification/verify_genesis_vii_c4_3_pack3a_constitutional_graph_foundation.py"
  "dev/verify_genesis_vii_c4_3_pack3a.sh"
  "docs/architecture/governance/constitutional_graph_foundation.md"
)

for path in "${required[@]}"; do
  test -f "${path}" || {
    echo "[FAIL] Missing ${path}"
    exit 1
  }
done
echo "[PASS] Genesis VII-C4.3 Pack 3A canonical file set present"

test -f artifacts/audit/km0000-c4_3-pack2/constitutional_article_usage.json || {
  echo "[FAIL] Missing Pack 2 constitutional article usage artifact"
  exit 1
}
echo "[PASS] Pack 2 article intelligence source present"

"${PYTHON_BIN}" -m py_compile \
  core/governance/constitution/coverage/graph/*.py \
  tests/test_genesis_vii_c4_3_pack3a_constitutional_graph_foundation.py \
  dev/verification/verify_genesis_vii_c4_3_pack3a_constitutional_graph_foundation.py
echo "[PASS] Genesis VII-C4.3 Pack 3A Python compilation"

"${PROJECT_ROOT}/dev/verify_genesis_vii_c4_3_pack3a.sh"
