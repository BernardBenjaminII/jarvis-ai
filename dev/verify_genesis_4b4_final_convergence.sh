#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "========================================================================"
echo "JARVIS — GENESIS IV-B4 FINAL CANONICAL OBSERVATION CONVERGENCE"
echo "========================================================================"

"$PYTHON_BIN" -m py_compile \
  core/observation/migration_registry.py \
  core/observation/audit.py \
  core/observation/__init__.py \
  core/observation/export_audit.py \
  tests/test_genesis_iv_b4_final_canonical_convergence.py \
  dev/verification/verify_genesis_iv_b4_final_convergence.py

echo "[PASS] Python compilation"

"$PYTHON_BIN" -m unittest -v \
  tests.test_genesis_iv_b4_final_canonical_convergence

"$PYTHON_BIN" \
  dev/verification/verify_genesis_iv_b4_final_convergence.py

echo
echo "[INFO] Running available Observation convergence regressions..."

REGRESSION_MODULES=(
  "tests.test_genesis_iv_b4c_migration_registry_reconstruction"
  "tests.test_genesis_iv_b4_audit_correction"
  "tests.test_genesis_iv_b4b_behavioral_compatibility"
  "tests.test_genesis_iv_b4a1_context_repair"
  "tests.test_genesis_iv_b4a_certification_repair"
  "tests.test_genesis_iv_b3_canonical_observation_convergence"
  "tests.test_genesis_iv_b3_convergence_governance"
  "tests.test_genesis_iv_b4_observation_migration"
)

AVAILABLE_MODULES=()
for module in "${REGRESSION_MODULES[@]}"; do
  path="${module//.//}.py"
  if [[ -f "$path" ]]; then
    AVAILABLE_MODULES+=("$module")
  fi
done

if (( ${#AVAILABLE_MODULES[@]} > 0 )); then
  "$PYTHON_BIN" -m unittest -v "${AVAILABLE_MODULES[@]}"
else
  echo "[INFO] No historical Observation regression modules found"
fi

OPTIONAL_VERIFIERS=(
  "dev/verification/verify_genesis_iv_b4c.py"
  "dev/verification/verify_genesis_iv_b4_audit_correction.py"
  "dev/verification/verify_genesis_iv_b4a1.py"
  "dev/verification/verify_genesis_iv_b4a.py"
  "dev/verification/verify_genesis_iv_b4.py"
)

for verifier in "${OPTIONAL_VERIFIERS[@]}"; do
  if [[ -f "$verifier" ]]; then
    echo "[INFO] Running $verifier"
    "$PYTHON_BIN" "$verifier"
  fi
done

if [[ -f "dev/report_genesis_iv_b4_migration.py" ]]; then
  "$PYTHON_BIN" dev/report_genesis_iv_b4_migration.py
fi

echo "------------------------------------------------------------------------"
echo "Checks failed : 0"
echo "Overall status: EXCELLENT"
echo "========================================================================"
