#!/usr/bin/env bash
set -euo pipefail
PACKAGE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_ROOT"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP=".migration_backups/genesis_iv_b3_${STAMP}"
FILES=(
 core/observation/__init__.py core/observation/adapters.py core/observation/audit.py
 core/observation/contracts.py core/observation/enums.py core/observation/errors.py
 core/observation/serialization.py
 tests/test_genesis_iv_b3_canonical_observation_convergence.py
 dev/verification/verify_genesis_iv_b3.py dev/verify_genesis_4b3.sh
 docs/architecture/convergence/genesis_iv_b3_canonical_observation_convergence.md
 docs/decisions/ADR-0038-canonical-observation-convergence.md
 standards/executive/OCS-0000.md
)
echo "========================================================================"
echo "JARVIS — INSTALL GENESIS IV-B3 CANONICAL OBSERVATION CONVERGENCE"
echo "========================================================================"
for rel in "${FILES[@]}"; do
  src="$PACKAGE_ROOT/$rel"; dst="$PROJECT_ROOT/$rel"
  [[ -f "$src" ]] || { echo "[FAIL] Missing package artifact: $rel"; exit 1; }
  if [[ -f "$dst" ]]; then
    mkdir -p "$BACKUP/$(dirname "$rel")"
    cp -a "$dst" "$BACKUP/$rel"
  fi
  mkdir -p "$(dirname "$dst")"
  cp -a "$src" "$dst"
  echo "[PASS] Installed $rel"
done
chmod +x dev/verify_genesis_4b3.sh
echo "[PASS] Backup root: $BACKUP"
echo "[PASS] Installation complete"
echo "Verify with: PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python ./dev/verify_genesis_4b3.sh"
