#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "========================================================================"
echo "JARVIS — GENESIS IV-B4A CERTIFICATION REPAIR"
echo "========================================================================"

"$PYTHON_BIN" -m py_compile \
  core/observation/__init__.py \
  core/observation/adapters.py \
  tests/test_genesis_iv_b4a_certification_repair.py \
  dev/verification/verify_genesis_iv_b4a.py

echo "[PASS] Python compilation"

"$PYTHON_BIN" -m unittest -v \
  tests.test_genesis_iv_b4a_certification_repair

"$PYTHON_BIN" dev/verification/verify_genesis_iv_b4a.py

echo
echo "[INFO] Running complete IV-B4 certification..."
"$PYTHON_BIN" -m unittest -v \
  tests.test_genesis_iv_b3_canonical_observation_convergence \
  tests.test_genesis_iv_b3_convergence_governance \
  tests.test_genesis_iv_b4_observation_migration

"$PYTHON_BIN" dev/verification/verify_genesis_iv_b4.py
"$PYTHON_BIN" dev/report_genesis_iv_b4_migration.py

echo "------------------------------------------------------------------------"
echo "Checks failed : 0"
echo "Overall status: EXCELLENT"
echo "========================================================================"
