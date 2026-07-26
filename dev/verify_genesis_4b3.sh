#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "========================================================================"
echo "JARVIS — GENESIS IV-B3 CANONICAL OBSERVATION CONVERGENCE"
echo "========================================================================"

"$PYTHON_BIN" -m py_compile \
  core/observation/__init__.py \
  core/observation/adapters.py \
  core/observation/audit.py \
  core/observation/contracts.py \
  core/observation/enums.py \
  core/observation/errors.py \
  core/observation/serialization.py \
  dev/report_genesis_iv_b3_convergence.py \
  dev/verification/verify_genesis_iv_b3.py \
  tests/test_genesis_iv_b3_canonical_observation_convergence.py \
  tests/test_genesis_iv_b3_convergence_governance.py

echo "[PASS] Python compilation"

"$PYTHON_BIN" -m unittest -v \
  tests.test_genesis_iv_b3_canonical_observation_convergence \
  tests.test_genesis_iv_b3_convergence_governance

"$PYTHON_BIN" dev/verification/verify_genesis_iv_b3.py

echo "------------------------------------------------------------------------"
echo "Checks failed : 0"
echo "Overall status: EXCELLENT"
echo "========================================================================"
