#!/usr/bin/env bash
set -euo pipefail

PACK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${1:-$(pwd)}"

if [[ ! -d "$PROJECT_ROOT/core" || ! -d "$PROJECT_ROOT/tests" ]]; then
    echo "[FAIL] Target is not a JARVIS repository: $PROJECT_ROOT" >&2
    exit 1
fi

cp -a "$PACK_ROOT/payload/." "$PROJECT_ROOT/"
chmod +x "$PROJECT_ROOT/dev/verify_convergence_c5.sh"

echo "[PASS] Convergence C-5A certification repair installed into $PROJECT_ROOT"
