#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "========================================================================"
echo "JARVIS — GENESIS IV-B4 OBSERVATION MIGRATION & COMPATIBILITY"
echo "========================================================================"

"$PYTHON_BIN" -m py_compile \
  core/observation/audit.py \
  core/observation/adapters.py \
  core/observation/migration.py \
  core/observation/migration_registry.py \
  core/observation/compatibility.py \
  dev/report_genesis_iv_b4_migration.py \
  dev/verification/verify_genesis_iv_b4.py \
  tests/test_genesis_iv_b4_observation_migration.py

echo "[PASS] Python compilation"

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
