#!/usr/bin/env bash
set -euo pipefail
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"; cd "$ROOT"; TS="$(date -u +%Y%m%dT%H%M%SZ)"; BAK=".migration_backups/genesis_iv_a7_${TS}"
FILES=(core/cognition/executive_decision/__init__.py core/cognition/executive_decision/contracts.py core/cognition/executive_decision/engine.py core/cognition/executive_decision/enums.py core/cognition/executive_decision/errors.py core/cognition/executive_decision/scoring.py core/cognition/executive_decision/serialization.py tests/test_genesis_iv_a7_executive_decision_engine.py docs/architecture/genesis_iv_a7_executive_decision_engine.md docs/decisions/ADR-0034-executive-decision-engine.md dev/verification/verify_genesis_iv_a7.py dev/verify_genesis_4a7.sh)
echo '========================================================================'; echo 'INSTALL GENESIS IV-A7'; echo '========================================================================'
for f in "${FILES[@]}"; do [[ -f "$PKG/$f" ]] || { echo "[FAIL] Missing $f"; exit 1; }; if [[ -f "$ROOT/$f" ]]; then mkdir -p "$BAK/$(dirname "$f")"; cp -a "$ROOT/$f" "$BAK/$f"; fi; mkdir -p "$ROOT/$(dirname "$f")"; cp -a "$PKG/$f" "$ROOT/$f"; echo "[PASS] $f"; done
chmod +x dev/verify_genesis_4a7.sh
echo "[PASS] Backup root: $BAK"; echo '[PASS] Installation complete'; echo 'Run: ./dev/verify_genesis_4a7.sh'
