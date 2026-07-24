#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/media/abdullah/JARVISDATA/Projects/jarvis-ai}"
PACK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAYLOAD_ROOT="$PACK_ROOT/payload"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_ROOT="$PROJECT_ROOT/.migration_backups/convergence_c1_$STAMP"

if [[ ! -d "$PROJECT_ROOT/core" || ! -d "$PROJECT_ROOT/tests" ]]; then
  echo "ERROR: JARVIS project root not found: $PROJECT_ROOT" >&2
  exit 1
fi

mkdir -p "$BACKUP_ROOT"
while IFS= read -r -d '' source; do
  relative="${source#$PAYLOAD_ROOT/}"
  target="$PROJECT_ROOT/$relative"
  if [[ -e "$target" ]]; then
    mkdir -p "$BACKUP_ROOT/$(dirname "$relative")"
    cp -a "$target" "$BACKUP_ROOT/$relative"
  fi
  mkdir -p "$(dirname "$target")"
  cp -a "$source" "$target"
done < <(find "$PAYLOAD_ROOT" -type f -print0)

chmod +x "$PROJECT_ROOT/dev/verify_convergence_c1.sh"

echo "Installed JARVIS Convergence C-1."
echo "Backup: $BACKUP_ROOT"
echo
echo "Verify with:"
echo "  PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python ./dev/verify_convergence_c1.sh"
