#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$ROOT"

echo "========================================================================"
echo "JARVIS — GENESIS UI-A EXECUTIVE INTEGRATION PACK"
echo "========================================================================"

required_files=(
  "docs/architecture/executive_integration_architecture.md"
  "docs/architecture/executive_projection_contract.md"
  "docs/architecture/capability_visibility_contract.md"
  "docs/architecture/knowledge_awareness_contract.md"
  "docs/decisions/ADR-EXEC-0001-canonical-integration-plane.md"
  "docs/plans/genesis_ui_a_execution_plan.md"
  "docs/plans/executive_integration_acceptance_criteria.md"
  "config/executive_integration_manifest.yaml"
  "config/subsystem_api_matrix.yaml"
  "dev/audit_executive_integration.py"
)

failures=0

for file in "${required_files[@]}"; do
  if [[ -f "$file" ]]; then
    echo "[PASS] $file"
  else
    echo "[FAIL] Missing: $file"
    failures=$((failures + 1))
  fi
done

if "$PYTHON_BIN" -m py_compile dev/audit_executive_integration.py; then
  echo "[PASS] Audit script compilation"
else
  echo "[FAIL] Audit script compilation"
  failures=$((failures + 1))
fi

if "$PYTHON_BIN" dev/audit_executive_integration.py; then
  echo "[PASS] Executive integration audit"
else
  echo "[FAIL] Executive integration audit"
  failures=$((failures + 1))
fi

for output in \
  docs/audits/executive_integration_audit.md \
  docs/audits/executive_integration_audit.json \
  docs/audits/executive_integration_matrix.csv
do
  if [[ -s "$output" ]]; then
    echo "[PASS] Generated $output"
  else
    echo "[FAIL] Missing or empty output: $output"
    failures=$((failures + 1))
  fi
done

echo "------------------------------------------------------------------------"
echo "Checks failed : $failures"

if [[ "$failures" -eq 0 ]]; then
  echo "Overall status: EXCELLENT"
  echo "========================================================================"
  exit 0
fi

echo "Overall status: FAILED"
echo "========================================================================"
exit 1
