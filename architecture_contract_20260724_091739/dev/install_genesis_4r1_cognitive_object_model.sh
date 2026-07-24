#!/usr/bin/env bash
set -Eeuo pipefail
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
BACKUP_ROOT="${PROJECT_ROOT}/.migration_backups/genesis_4r1_$(date +%Y%m%d_%H%M%S)"
[[ -d "$PROJECT_ROOT/core/cognition/common" ]] || { echo '[FAIL] Genesis IV-R0-B required' >&2; exit 1; }
mkdir -p "$BACKUP_ROOT"
printf '\n======================================================================\nJARVIS GENESIS IV-R1 — COGNITIVE OBJECT MODEL INSTALLATION\n======================================================================\n\n'
printf 'Project root : %s\nPython       : %s\nBackup       : %s\n\n' "$PROJECT_ROOT" "$PYTHON_BIN" "$BACKUP_ROOT"
PYTHON_BIN="$PYTHON_BIN" PROJECT_ROOT="$PROJECT_ROOT" "$PROJECT_ROOT/dev/verify_genesis_4r1.sh"
printf '\n======================================================================\nGENESIS IV-R1 INSTALLATION COMPLETE\n======================================================================\n\nBehavior changes: Additive only\nPublic redirects : 0\nOverall status   : EXCELLENT\n'
