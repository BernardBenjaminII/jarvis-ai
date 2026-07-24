#!/usr/bin/env bash
set -euo pipefail
PACK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_ROOT="$PROJECT_ROOT/.migration_backups/convergence_c4_$STAMP"

if [[ ! -d "$PROJECT_ROOT/core" || ! -d "$PROJECT_ROOT/dev" ]]; then
  echo "ERROR: PROJECT_ROOT does not look like the JARVIS repository: $PROJECT_ROOT" >&2
  exit 1
fi

mkdir -p "$BACKUP_ROOT"
while IFS= read -r rel; do
  [[ -z "$rel" ]] && continue
  src="$PACK_ROOT/payload/$rel"
  dst="$PROJECT_ROOT/$rel"
  if [[ -e "$dst" ]]; then
    mkdir -p "$BACKUP_ROOT/$(dirname "$rel")"
    cp -a "$dst" "$BACKUP_ROOT/$rel"
  fi
  mkdir -p "$(dirname "$dst")"
  cp -a "$src" "$dst"
done < "$PACK_ROOT/manifest.txt"
chmod +x "$PROJECT_ROOT/dev/verify_convergence_c4.sh"
echo "[PASS] JARVIS Convergence C-4 installed"
echo "Backup: $BACKUP_ROOT"
echo "Verify: PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python ./dev/verify_convergence_c4.sh"
