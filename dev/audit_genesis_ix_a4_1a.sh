#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${ROOT}"
exec "${PYTHON_BIN}"   dev/audits/audit_genesis_ix_a4_1a_executive_conversation_inventory.py   --root "${ROOT}" "$@"
