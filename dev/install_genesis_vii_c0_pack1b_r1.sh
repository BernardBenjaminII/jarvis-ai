#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
required=(
 core/governance/audit/models.py core/governance/audit/filesystem.py core/governance/audit/inventory.py
 core/governance/audit/verification.py core/governance/audit/__init__.py
 dev/verification/verify_genesis_vii_c0_pack1b_r1.py tests/test_genesis_vii_c0_pack1b_r1.py
 dev/verify_genesis_vii_c0_pack1b_r1.sh
)
for path in "${required[@]}"; do [[ -f "$path" ]] || { echo "[FAIL] Missing Pack 1B-R1 file: $path" >&2; exit 1; }; done
chmod +x dev/verify_genesis_vii_c0_pack1b_r1.sh dev/install_genesis_vii_c0_pack1b_r1.sh
mkdir -p artifacts/audit/km0000-r1
echo "[PASS] Genesis VII-C0 Pack 1B-R1 file set present"
PYTHON_BIN="$PYTHON_BIN" ./dev/verify_genesis_vii_c0_pack1b_r1.sh
