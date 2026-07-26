#!/usr/bin/env bash
set -euo pipefail

PACKAGE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_ROOT"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_ROOT=".migration_backups/genesis_iv_a8_${TIMESTAMP}"

FILES=(
  "core/cognition/mission_compiler/__init__.py"
  "core/cognition/mission_compiler/compiler.py"
  "core/cognition/mission_compiler/contracts.py"
  "core/cognition/mission_compiler/enums.py"
  "core/cognition/mission_compiler/errors.py"
  "core/cognition/mission_compiler/graph.py"
  "core/cognition/mission_compiler/serialization.py"
  "tests/test_genesis_iv_a8_executive_mission_compiler.py"
  "docs/architecture/genesis_iv_a8_executive_mission_compiler.md"
  "docs/decisions/ADR-0035-executive-mission-compiler-boundary.md"
  "dev/verification/verify_genesis_iv_a8.py"
  "dev/verify_genesis_4a8.sh"
)

echo "========================================================================"
echo "JARVIS — INSTALL GENESIS IV-A8 EXECUTIVE MISSION COMPILER"
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

chmod +x dev/verify_genesis_4a8.sh

echo "[PASS] Backup root: $BACKUP_ROOT"
echo "[PASS] Genesis IV-A8 installation complete"
echo
echo "Verify with:"
echo "  PYTHON_BIN=\${PYTHON_BIN:-python3} ./dev/verify_genesis_4a8.sh"
echo "========================================================================"
