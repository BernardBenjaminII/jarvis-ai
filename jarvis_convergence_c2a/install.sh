#!/usr/bin/env bash
set -euo pipefail

PACK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
PAYLOAD="$PACK_ROOT/payload"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$PROJECT_ROOT/.migration_backups/convergence_c2a_$STAMP"

[[ -d "$PROJECT_ROOT/core" ]] || { echo "ERROR: Not a JARVIS project root: $PROJECT_ROOT" >&2; exit 1; }
[[ -f "$PROJECT_ROOT/core/conversation/orchestrator.py" ]] || { echo "ERROR: Convergence C-2 is not installed." >&2; exit 1; }
[[ -f "$PROJECT_ROOT/tests/test_convergence_c1_http_contract.py" ]] || { echo "ERROR: C-1 HTTP contract is missing." >&2; exit 1; }

mkdir -p "$BACKUP"
while IFS= read -r -d '' source; do
    rel="${source#$PAYLOAD/}"
    target="$PROJECT_ROOT/$rel"
    if [[ -e "$target" ]]; then
        mkdir -p "$BACKUP/$(dirname "$rel")"
        cp -a "$target" "$BACKUP/$rel"
    fi
    mkdir -p "$(dirname "$target")"
    cp -a "$source" "$target"
done < <(find "$PAYLOAD" -type f -print0)

chmod +x "$PROJECT_ROOT/dev/verify_convergence_c2a.sh"

echo "Installed JARVIS Convergence C-2A — Certification Repair"
echo "Backup: $BACKUP"
echo
echo "Verify with:"
echo "  PYTHON_BIN=python ./dev/verify_convergence_c2a.sh"
