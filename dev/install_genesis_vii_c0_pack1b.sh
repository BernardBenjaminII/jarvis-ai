#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
cd "$PROJECT_ROOT"

required=(
  core/governance/audit/inventory.py
  core/governance/audit/models.py
  core/governance/audit/filesystem.py
  core/governance/audit/python_parser.py
  core/governance/audit/markdown_parser.py
  core/governance/audit/verification.py
  dev/verification/verify_genesis_vii_c0_pack1b.py
  tests/test_genesis_vii_c0_pack1b.py
)

for path in "${required[@]}"; do
  if [[ ! -f "$path" ]]; then
    echo "[FAIL] Missing Pack 1B file: $path" >&2
    exit 1
  fi
done

mkdir -p artifacts/audit/km0000-r1

echo "[PASS] Genesis VII-C0 Pack 1B file set present"
PYTHON_BIN="$PYTHON_BIN" ./dev/verify_genesis_vii_c0_pack1b.sh
