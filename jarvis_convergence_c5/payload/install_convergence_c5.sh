#!/usr/bin/env bash
set -euo pipefail
PACK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${1:-$(pwd)}"
cp -a "$PACK_ROOT/payload/." "$PROJECT_ROOT/"
chmod +x "$PROJECT_ROOT/dev/verify_convergence_c5.sh"
echo "[PASS] Convergence C-5 installed into $PROJECT_ROOT"
