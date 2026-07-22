#!/usr/bin/env bash
set -euo pipefail

BUNDLE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="${1:-$(pwd)}"

if [ ! -d "$PROJECT_ROOT" ]; then
    echo "ERROR: Project directory does not exist: $PROJECT_ROOT" >&2
    exit 1
fi

if [ ! -f "$PROJECT_ROOT/core/cognition/models.py" ]; then
    echo "ERROR: Genesis VI-A1 Step 1 is not installed in: $PROJECT_ROOT" >&2
    exit 1
fi

echo
echo "Installing Genesis VI-A2 into:"
echo "  $PROJECT_ROOT"
echo

mkdir -p "$PROJECT_ROOT/core/cognition"
mkdir -p "$PROJECT_ROOT/tests"
mkdir -p "$PROJECT_ROOT/dev/verification"
mkdir -p "$PROJECT_ROOT/docs/architecture/cognition"

cp -f "$BUNDLE_ROOT/core/cognition/working_memory.py"     "$PROJECT_ROOT/core/cognition/working_memory.py"

cp -f "$BUNDLE_ROOT/core/cognition/__init__.py"     "$PROJECT_ROOT/core/cognition/__init__.py"

cp -f "$BUNDLE_ROOT/tests/test_genesis_vi_a2_working_memory.py"     "$PROJECT_ROOT/tests/test_genesis_vi_a2_working_memory.py"

cp -f "$BUNDLE_ROOT/dev/verification/verify_genesis_vi_a2.py"     "$PROJECT_ROOT/dev/verification/verify_genesis_vi_a2.py"

cp -f "$BUNDLE_ROOT/dev/verify_genesis_vi_a2.sh"     "$PROJECT_ROOT/dev/verify_genesis_vi_a2.sh"

cp -f "$BUNDLE_ROOT/docs/architecture/cognition/genesis_vi_a2_working_memory.md"     "$PROJECT_ROOT/docs/architecture/cognition/genesis_vi_a2_working_memory.md"

chmod +x "$PROJECT_ROOT/dev/verify_genesis_vi_a2.sh"
chmod +x "$PROJECT_ROOT/dev/verification/verify_genesis_vi_a2.py"

echo "[PASS] Genesis VI-A2 installed"
