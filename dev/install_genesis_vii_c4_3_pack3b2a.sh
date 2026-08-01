#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
export PYTHONPATH="${PROJECT_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
cd "${PROJECT_ROOT}"
required=(
"core/governance/constitution/coverage/graph/repository_contracts.py"
"core/governance/constitution/coverage/graph/repository_models.py"
"core/governance/constitution/coverage/graph/repository_classifier.py"
"core/governance/constitution/coverage/graph/repository_builder.py"
"core/governance/constitution/coverage/graph/repository_integrity.py"
"core/governance/constitution/coverage/graph/repository_metrics.py"
"core/governance/constitution/coverage/graph/repository_graph.py"
"core/governance/constitution/coverage/graph/repository_engine.py"
"core/governance/constitution/coverage/graph/repository_reporting.py"
"core/governance/constitution/coverage/graph/repository_queries.py"
"core/governance/constitution/coverage/graph/repository_public_api.py"
"tests/test_genesis_vii_c4_3_pack3b2a_repository_projection.py"
"dev/verification/verify_genesis_vii_c4_3_pack3b2a_repository_projection.py"
"dev/verify_genesis_vii_c4_3_pack3b2a.sh"
"docs/architecture/governance/constitutional_repository_projection.md")
for path in "${required[@]}"; do test -f "$path" || { echo "[FAIL] Missing $path"; exit 1; }; done
echo "[PASS] Genesis VII-C4.3 Pack 3B-2A canonical file set present"
test -f artifacts/audit/km0000-c4_3-pack3b1/constitutional_authority_graph.json || { echo "[FAIL] Missing Pack 3B-1 constitutional authority graph artifact"; exit 1; }
echo "[PASS] Pack 3B-1 authority graph source present"
"${PYTHON_BIN}" -m py_compile core/governance/constitution/coverage/graph/repository_*.py tests/test_genesis_vii_c4_3_pack3b2a_repository_projection.py dev/verification/verify_genesis_vii_c4_3_pack3b2a_repository_projection.py
echo "[PASS] Genesis VII-C4.3 Pack 3B-2A Python compilation"
"${PROJECT_ROOT}/dev/verify_genesis_vii_c4_3_pack3b2a.sh"
