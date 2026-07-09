#!/usr/bin/env bash
set -euo pipefail

REQ_DIR="requirements"
OLD="knowledge_engine.txt"
NEW="knowledge.txt"

echo "======================================"
echo "Fixing JARVIS requirements references"
echo "======================================"

for file in \
    "$REQ_DIR/linux.txt" \
    "$REQ_DIR/windows.txt" \
    "$REQ_DIR/macos.txt"
do
    if [[ ! -f "$file" ]]; then
        echo "Skipping missing file: $file"
        continue
    fi

    cp "$file" "$file.bak"

    sed -i "s/${OLD}/${NEW}/g" "$file"

    echo "✓ Updated $file"
done

echo
echo "Verifying..."

if grep -R "${OLD}" "$REQ_DIR"; then
    echo
    echo "❌ Some stale references remain."
    exit 1
else
    echo "✓ No remaining references to ${OLD}"
fi

echo
echo "Current include statements:"
grep -Rn "knowledge.txt" "$REQ_DIR"

echo
echo "Done."
echo
echo "Next step:"
echo "  /media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \\"
echo "      -m pip install -r requirements/linux.txt"
