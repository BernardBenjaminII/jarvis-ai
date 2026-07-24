#!/usr/bin/env bash
set -euo pipefail
PACK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$PROJECT_ROOT/.migration_backups/convergence_c3_$STAMP"
files=(core/executive/routing.py core/executive/planner.py tests/test_convergence_c3_capability_routing.py docs/architecture/convergence_c3_capability_routing.md dev/verification/verify_convergence_c3.py dev/verify_convergence_c3.sh)
mkdir -p "$BACKUP"
for rel in "${files[@]}"; do
 src="$PACK_ROOT/payload/$rel"; dst="$PROJECT_ROOT/$rel"
 if [[ -f "$dst" ]]; then mkdir -p "$BACKUP/$(dirname "$rel")"; cp -a "$dst" "$BACKUP/$rel"; fi
 mkdir -p "$(dirname "$dst")"; cp -a "$src" "$dst"
done
chmod +x "$PROJECT_ROOT/dev/verify_convergence_c3.sh"
echo "[PASS] Installed JARVIS Convergence C-3"
echo "Backup: $BACKUP"
