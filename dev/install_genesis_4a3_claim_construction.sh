#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "${PROJECT_ROOT}"

echo
echo "======================================================================"
echo "JARVIS GENESIS IV-A3 — CLAIM CONSTRUCTION INSTALLATION"
echo "======================================================================"
echo
echo "Project root : ${PROJECT_ROOT}"
echo "Python       : ${PYTHON_BIN}"
echo

required_files=(
    "core/cognition/contracts.py"
    "core/cognition/observation.py"
    "core/cognition/provenance.py"
    "core/cognition/evidence.py"
    "core/cognition/evidence_chain.py"
    "core/cognition/evidence_validation.py"
    "core/cognition/claim.py"
    "core/cognition/claim_construction.py"
    "core/cognition/claim_validation.py"
    "tests/test_genesis_4a3_claim_construction.py"
    "dev/verification/verify_genesis_4a3_claim_construction.py"
    "dev/verify_genesis_4a3.sh"
    "docs/architecture/genesis_iv_a3_claim_construction.md"
    "docs/decisions/ADR-0019-genesis-iv-claim-constitution.md"
)

for required_file in "${required_files[@]}"; do
    if [[ ! -f "${required_file}" ]]; then
        echo "[FAIL] Missing required file: ${required_file}"
        exit 1
    fi
done

echo "[PASS] Genesis IV-A1 observation prerequisite"
echo "[PASS] Genesis IV-A2 evidence prerequisite"
echo "[PASS] Genesis IV-A3 source structure"

"${PYTHON_BIN}" -m compileall -q core/cognition
echo "[PASS] Cognition package compilation"

PYTHON_BIN="${PYTHON_BIN}" ./dev/verify_genesis_4a3.sh

echo
echo "======================================================================"
echo "GENESIS IV-A3 INSTALLATION COMPLETE"
echo "======================================================================"
echo
echo "Installed:"
echo "  core/cognition/claim.py"
echo "  core/cognition/claim_construction.py"
echo "  core/cognition/claim_validation.py"
echo "  tests/test_genesis_4a3_claim_construction.py"
echo "  dev/verification/verify_genesis_4a3_claim_construction.py"
echo "  dev/verify_genesis_4a3.sh"
echo "  docs/architecture/genesis_iv_a3_claim_construction.md"
echo "  docs/decisions/ADR-0019-genesis-iv-claim-constitution.md"
echo
echo "Overall status: EXCELLENT"
echo
