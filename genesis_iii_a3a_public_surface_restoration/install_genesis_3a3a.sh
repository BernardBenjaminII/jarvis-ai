#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 /absolute/path/to/jarvis-ai" >&2
    exit 2
fi

TARGET="$(realpath "$1")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAYLOAD="$SCRIPT_DIR/payload"

if [[ ! -d "$TARGET/core/cognition/workspace" ]]; then
    echo "ERROR: target does not contain core/cognition/workspace: $TARGET" >&2
    exit 1
fi

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$TARGET/.migration_backups/genesis_3a3a_$STAMP"
mkdir -p "$BACKUP/core/cognition"

if [[ -f "$TARGET/core/cognition/__init__.py" ]]; then
    cp -a "$TARGET/core/cognition/__init__.py" "$BACKUP/core/cognition/__init__.py"
fi

mkdir -p \
    "$TARGET/core/cognition" \
    "$TARGET/tests" \
    "$TARGET/dev/verification" \
    "$TARGET/docs/architecture"

cp -a "$PAYLOAD/core/cognition/__init__.py" "$TARGET/core/cognition/__init__.py"
cp -a "$PAYLOAD/tests/test_genesis_3a3a_cognitive_workspace_public_surface.py" "$TARGET/tests/"
cp -a "$PAYLOAD/dev/verification/verify_genesis_3a3a.py" "$TARGET/dev/verification/"
cp -a "$PAYLOAD/dev/verify_genesis_3a3a.sh" "$TARGET/dev/"
cp -a "$PAYLOAD/docs/architecture/genesis_3a3a_cognitive_workspace_public_surface_restoration.md" "$TARGET/docs/architecture/"
chmod +x "$TARGET/dev/verify_genesis_3a3a.sh" "$TARGET/dev/verification/verify_genesis_3a3a.py"

printf '[PASS] Genesis III-A3A installed\nBackup: %s\n' "$BACKUP"
