#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
export PYTHONPATH="${PROJECT_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
cd "${PROJECT_ROOT}"
required=(core/governance/constitution/coverage/graph/directorate_authority.py core/governance/constitution/coverage/graph/directorate_capabilities.py core/governance/constitution/coverage/graph/directorate_review.py core/governance/constitution/coverage/graph/directorate_impact.py core/governance/constitution/coverage/graph/directorate_governance.py core/governance/constitution/coverage/graph/directorate_api.py tests/test_genesis_vii_c4_3_pack3b2b3_executive_governance.py dev/verification/verify_genesis_vii_c4_3_pack3b2b3_executive_governance.py dev/verify_genesis_vii_c4_3_pack3b2b3.sh docs/architecture/governance/constitutional_executive_governance.md)
for path in "${required[@]}"; do test -f "$path" || { echo "[FAIL] Missing $path"; exit 1; }; done
echo '[PASS] Genesis VII-C4.3 Pack 3B-2B.3 canonical file set present'
test -f artifacts/audit/km0000-c4_3-pack3b2b1/constitutional_directorate_foundation.json || { echo '[FAIL] Missing Pack 3B-2B.1 source artifact'; exit 1; }
echo '[PASS] Pack 3B-2B.1 source artifact present'
test -f artifacts/audit/km0000-c4_3-pack3b2b2/constitutional_directorate_projection.json || { echo '[FAIL] Missing certified Pack 3B-2B.2 projection artifact'; exit 1; }
echo '[PASS] Certified Pack 3B-2B.2 projection artifact present'
"${PYTHON_BIN}" -m py_compile core/governance/constitution/coverage/graph/directorate_authority.py core/governance/constitution/coverage/graph/directorate_capabilities.py core/governance/constitution/coverage/graph/directorate_review.py core/governance/constitution/coverage/graph/directorate_impact.py core/governance/constitution/coverage/graph/directorate_governance.py core/governance/constitution/coverage/graph/directorate_api.py core/governance/constitution/coverage/graph/directorate_queries.py tests/test_genesis_vii_c4_3_pack3b2b3_executive_governance.py dev/verification/verify_genesis_vii_c4_3_pack3b2b3_executive_governance.py
echo '[PASS] Genesis VII-C4.3 Pack 3B-2B.3 Python compilation'
"${PROJECT_ROOT}/dev/verify_genesis_vii_c4_3_pack3b2b3.sh"
