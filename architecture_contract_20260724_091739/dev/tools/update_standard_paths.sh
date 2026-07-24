#!/usr/bin/env bash
#
# ======================================================================
# JARVIS Engineering Standards Path Migration
#
# Updates all references from:
#   docs/standards/FP-0000_First_Principles.md
#
# to:
#   docs/standards/foundation/FP-0000_First_Principles.md
#
# Safe to run multiple times.
# ======================================================================

set -euo pipefail

OLD_PATH="docs/standards/FP-0000_First_Principles.md"
NEW_PATH="docs/standards/foundation/FP-0000_First_Principles.md"

echo
echo "=============================================================="
echo "JARVIS Standards Reference Migration"
echo "=============================================================="
echo "Old : $OLD_PATH"
echo "New : $NEW_PATH"
echo

UPDATED=0

while IFS= read -r -d '' FILE
do
    if grep -qF "$OLD_PATH" "$FILE"; then

        echo "Updating: $FILE"

        sed -i \
            "s|$OLD_PATH|$NEW_PATH|g" \
            "$FILE"

        UPDATED=$((UPDATED+1))
    fi

done < <(
    find docs \
        -type f \
        \( \
            -name "*.md" \
            -o -name "*.txt" \
            -o -name "*.rst" \
        \) \
        -print0
)

echo
echo "--------------------------------------------------------------"
echo "Files Updated : $UPDATED"
echo "--------------------------------------------------------------"
echo

echo "Remaining references (should be empty):"
echo

grep -RFn "$OLD_PATH" docs || true

echo
echo "Migration complete."
echo
