#!/usr/bin/env bash
set -euo pipefail

ROOT="/media/abdullah/JARVISDATA/Projects/jarvis-ai"
UI="$ROOT/core/src/static/mission_control"

LATEST="$(
    find "$ROOT/.ui_backups" \
        -maxdepth 1 \
        -type d \
        -name 'conversation_first_visual_r3_3_*' \
        -printf '%T@ %p\n' \
        | sort -nr \
        | head -1 \
        | cut -d' ' -f2-
)"

[[ -n "$LATEST" ]] || {
    echo "FAIL: no R3.3 backup found."
    exit 1
}

echo "Rolling back R3.3 from:"
echo "  $LATEST"

cp -a \
    "$LATEST/index.html" \
    "$UI/index.html"

rm -f \
    "$UI/conversation_first_r3_3.css" \
    "$UI/conversation_first_r3_3.js"

echo
echo "PASS: R3.3 removed."
echo "R3.2.2 structural baseline restored."
echo
echo "Hard-refresh /bridge."
