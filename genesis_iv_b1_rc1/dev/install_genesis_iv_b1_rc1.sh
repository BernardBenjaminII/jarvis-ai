#!/usr/bin/env bash
set -euo pipefail
PACKAGE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_ROOT"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_ROOT=".migration_backups/genesis_iv_b1_rc1_${TIMESTAMP}"
FILES=(
  core/integration/__init__.py core/integration/api.py core/integration/audit.py core/integration/catalog.py core/integration/cli.py core/integration/contracts.py core/integration/enums.py core/integration/errors.py core/integration/knowledge.py core/integration/projections.py core/integration/registry.py core/integration/serialization.py core/integration/service.py
  tests/test_genesis_iv_b1_executive_integration_visibility_fabric.py
  docs/architecture/genesis_iv_b1_executive_integration_visibility_fabric.md
  docs/decisions/ADR-0037-executive-integration-visibility-fabric.md
  dev/verification/verify_genesis_iv_b1.py dev/verify_genesis_4b1.sh
)
echo "========================================================================"
echo "JARVIS — INSTALL GENESIS IV-B1 RC1 INTEGRATION AND VISIBILITY FABRIC"
echo "========================================================================"
for relative in "${FILES[@]}"; do
  source_file="$PACKAGE_ROOT/$relative"; target_file="$PROJECT_ROOT/$relative"
  [[ -f "$source_file" ]] || { echo "[FAIL] Package artifact missing: $relative"; exit 1; }
  if [[ -f "$target_file" ]]; then mkdir -p "$BACKUP_ROOT/$(dirname "$relative")"; cp -a "$target_file" "$BACKUP_ROOT/$relative"; fi
  mkdir -p "$(dirname "$target_file")"; cp -a "$source_file" "$target_file"; echo "[PASS] Installed $relative"
done
chmod +x dev/verify_genesis_4b1_rc1.sh
echo "[PASS] Backup root: $BACKUP_ROOT"
echo "[PASS] Genesis IV-B1 RC1 installation complete"
echo "Verify: PYTHON_BIN=\${PYTHON_BIN:-python3} ./dev/verify_genesis_4b1_rc1.sh"
echo "Audit:  PYTHON_BIN=\${PYTHON_BIN:-python3} -m core.integration.cli audit --repository-root . --output docs/audits/genesis_iv_b1_integration_audit.json"
