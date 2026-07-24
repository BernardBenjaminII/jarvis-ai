#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$ROOT"

echo "========================================================================"
echo "INSTALLING JARVIS — GENESIS UI-A3 CAPABILITY DISCOVERY & REGISTRATION"
echo "========================================================================"

required=(
  "core/capabilities/__init__.py"
  "core/capabilities/discovery.py"
  "core/capabilities/metadata.py"
  "core/capabilities/operations.py"
  "core/integration/bootstrap.py"
  "core/integration/providers/capabilities.py"
  "core/integration/providers/operations.py"
  "tests/test_genesis_ui_a3_capability_discovery_registration.py"
)

for file in "${required[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "[FAIL] Missing pack file: $file"
    exit 1
  fi
done

chmod +x \
  dev/verification/verify_genesis_ui_a3_capability_discovery_registration.py \
  dev/verify_genesis_ui_a3_capability_discovery_registration.sh

PYTHON_BIN="$PYTHON_BIN" \
./dev/verify_genesis_ui_a3_capability_discovery_registration.sh

echo
echo "[PASS] Genesis UI-A3 Capability Discovery & Registration installed"
