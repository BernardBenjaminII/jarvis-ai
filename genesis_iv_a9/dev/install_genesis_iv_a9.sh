#!/usr/bin/env bash
set -euo pipefail

PACKAGE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_ROOT"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_ROOT=".migration_backups/genesis_iv_a9_${TIMESTAMP}"

FILES=(
  "core/cognition/execution_orchestrator/__init__.py"
  "core/cognition/execution_orchestrator/contracts.py"
  "core/cognition/execution_orchestrator/enums.py"
  "core/cognition/execution_orchestrator/errors.py"
  "core/cognition/execution_orchestrator/executors.py"
  "core/cognition/execution_orchestrator/orchestrator.py"
  "core/cognition/execution_orchestrator/serialization.py"
  "core/cognition/execution_orchestrator/state.py"
  "tests/test_genesis_iv_a9_executive_execution_orchestrator.py"
  "docs/architecture/genesis_iv_a9_executive_execution_orchestrator.md"
  "docs/decisions/ADR-0036-executive-execution-orchestrator-boundary.md"
  "dev/verification/verify_genesis_iv_a9.py"
  "dev/verify_genesis_4a9.sh"
)

echo "========================================================================"
echo "JARVIS — INSTALL GENESIS IV-A9 EXECUTIVE EXECUTION ORCHESTRATOR"
echo "========================================================================"

for relative in "${FILES[@]}"; do
    source_file="$PACKAGE_ROOT/$relative"
    target_file="$PROJECT_ROOT/$relative"

    if [[ ! -f "$source_file" ]]; then
        echo "[FAIL] Package artifact missing: $relative"
        exit 1
    fi

    if [[ -f "$target_file" ]]; then
        mkdir -p "$BACKUP_ROOT/$(dirname "$relative")"
        cp -a "$target_file" "$BACKUP_ROOT/$relative"
    fi

    mkdir -p "$(dirname "$target_file")"
    cp -a "$source_file" "$target_file"
    echo "[PASS] Installed $relative"
done

chmod +x dev/verify_genesis_4a9.sh

echo "[PASS] Backup root: $BACKUP_ROOT"
echo "[PASS] Genesis IV-A9 installation complete"
echo
echo "Verify with:"
echo "  PYTHON_BIN=\${PYTHON_BIN:-python3} ./dev/verify_genesis_4a9.sh"
echo "========================================================================"
