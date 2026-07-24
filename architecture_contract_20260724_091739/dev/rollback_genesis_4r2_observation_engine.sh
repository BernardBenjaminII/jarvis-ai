#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
BACKUP_ROOT="${1:-}"

FILES=(
  "core/cognition/layers/observation/__init__.py"
  "core/cognition/layers/observation/conflicts.py"
  "core/cognition/layers/observation/director.py"
  "core/cognition/layers/observation/duplicates.py"
  "core/cognition/layers/observation/enums.py"
  "core/cognition/layers/observation/errors.py"
  "core/cognition/layers/observation/factory.py"
  "core/cognition/layers/observation/lifecycle.py"
  "core/cognition/layers/observation/merge.py"
  "core/cognition/layers/observation/models.py"
  "core/cognition/layers/observation/normalization.py"
  "core/cognition/layers/observation/query.py"
  "core/cognition/layers/observation/registry.py"
  "core/cognition/layers/observation/relationships.py"
  "core/cognition/layers/observation/validation.py"
  "tests/cognition/test_genesis_4r2_observation_models.py"
  "tests/cognition/test_genesis_4r2_observation_registry.py"
  "tests/cognition/test_genesis_4r2_observation_analysis.py"
  "tests/cognition/test_genesis_4r2_observation_director.py"
  "examples/cognition/observation_engine_demo.py"
  "docs/architecture/cognition/02_observation_engine.md"
  "docs/decisions/ADR-0022-observation-engine.md"
  "docs/history/0001_genesis_iv_first_major_release.md"
  "dev/verification/verify_genesis_4r2_observation_engine.py"
  "dev/verify_genesis_4r2.sh"
  "dev/migration_report_genesis_4r2.py"
)

[[ -n "$BACKUP_ROOT" ]] || {
  echo "Usage: $0 <backup-directory>" >&2
  exit 2
}

if [[ "$BACKUP_ROOT" != /* ]]; then
    BACKUP_ROOT="${PROJECT_ROOT}/${BACKUP_ROOT}"
fi

[[ -d "$BACKUP_ROOT" ]] || {
  echo "Backup directory not found: $BACKUP_ROOT" >&2
  exit 1
}

for relative in "${FILES[@]}"; do
    backup="${BACKUP_ROOT}/${relative}"
    destination="${PROJECT_ROOT}/${relative}"

    if [[ -f "$backup" ]]; then
        mkdir -p "$(dirname "$destination")"
        cp -a "$backup" "$destination"
        echo "[RESTORE] $relative"
    else
        rm -f "$destination"
        echo "[REMOVE] $relative"
    fi
done

find "${PROJECT_ROOT}/core/cognition/layers/observation" \
  -type d -empty -delete 2>/dev/null || true

echo
echo "Genesis IV-R2 rollback complete."
