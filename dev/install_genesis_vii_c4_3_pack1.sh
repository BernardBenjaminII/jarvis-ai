#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; PYTHON_BIN="${PYTHON_BIN:-python3}"; export PYTHONPATH="${ROOT}${PYTHONPATH:+:${PYTHONPATH}}"; cd "$ROOT"
required=(core/governance/constitution/coverage/__init__.py core/governance/constitution/coverage/contracts.py core/governance/constitution/coverage/engine.py core/governance/constitution/coverage/fingerprints.py core/governance/constitution/coverage/inventory.py core/governance/constitution/coverage/metrics.py core/governance/constitution/coverage/models.py core/governance/constitution/coverage/policies.py core/governance/constitution/coverage/reporting.py tests/test_genesis_vii_c4_3_pack1_coverage_intelligence_foundation.py dev/verification/verify_genesis_vii_c4_3_pack1_coverage_intelligence_foundation.py dev/verify_genesis_vii_c4_3_pack1.sh docs/architecture/governance/constitutional_coverage_intelligence_foundation.md)
for p in "${required[@]}"; do test -f "$p" || { echo "[FAIL] Missing $p"; exit 1; }; done; echo '[PASS] Genesis VII-C4.3 Pack 1 canonical file set present'
test -f artifacts/audit/km0000-c4_2/constitutional_repository_audit.json || { echo '[FAIL] Missing C4.2 audit'; exit 1; }
"$PYTHON_BIN" -m py_compile core/governance/constitution/coverage/*.py dev/verification/verify_genesis_vii_c4_3_pack1_coverage_intelligence_foundation.py tests/test_genesis_vii_c4_3_pack1_coverage_intelligence_foundation.py; echo '[PASS] Genesis VII-C4.3 Pack 1 Python compilation'
"$ROOT/dev/verify_genesis_vii_c4_3_pack1.sh"
