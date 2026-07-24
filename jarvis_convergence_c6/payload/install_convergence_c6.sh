#!/usr/bin/env bash
set -euo pipefail
TARGET="${1:-}"
if [[ -z "$TARGET" || ! -d "$TARGET" ]]; then
  echo "Usage: $0 /path/to/jarvis-ai" >&2; exit 2
fi
SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/payload"
cp -a "$SOURCE/." "$TARGET/"
chmod +x "$TARGET/dev/verify_convergence_c6.sh" "$TARGET/dev/verification/verify_convergence_c6.py"
echo "[PASS] Convergence C-6 installed into $TARGET"
