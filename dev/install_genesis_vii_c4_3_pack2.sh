#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
export PYTHONPATH="${ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
cd "${ROOT}"
required=(
 core/governance/constitution/coverage/article_intelligence.py
 core/governance/constitution/coverage/article_reporting.py
 core/governance/constitution/coverage/executive_queries.py
 tests/test_genesis_vii_c4_3_pack2_constitutional_article_intelligence.py
 dev/verification/verify_genesis_vii_c4_3_pack2_constitutional_article_intelligence.py
 dev/verify_genesis_vii_c4_3_pack2.sh
 docs/architecture/governance/constitutional_article_intelligence.md
)
for p in "${required[@]}"; do test -f "$p" || { echo "[FAIL] Missing $p"; exit 1; }; done
echo "[PASS] Genesis VII-C4.3 Pack 2 canonical file set present"
test -f artifacts/audit/km0000-c4_3-pack1/constitutional_coverage_metrics.json
test -f artifacts/audit/km0000-c4_3-pack1/constitutional_coverage_traceability.json
test -f artifacts/audit/km0000-c4_2/constitutional_repository_audit.json
test -f artifacts/audit/km0000-c4_2/constitutional_repository_inventory.json
"${PYTHON_BIN}" -m py_compile core/governance/constitution/coverage/*.py tests/test_genesis_vii_c4_3_pack2_constitutional_article_intelligence.py dev/verification/verify_genesis_vii_c4_3_pack2_constitutional_article_intelligence.py
echo "[PASS] Genesis VII-C4.3 Pack 2 Python compilation"
"${ROOT}/dev/verify_genesis_vii_c4_3_pack2.sh"
