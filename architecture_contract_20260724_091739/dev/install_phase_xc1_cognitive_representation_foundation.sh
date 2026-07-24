#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_ROOT"
PYTHON_BIN="${PYTHON_BIN:-python}"

required=(
  core/representation/__init__.py
  core/representation/contracts.py
  core/representation/segmentation.py
  tests/test_phase_xc1_cognitive_representation.py
  dev/verification/verify_phase_xc1_cognitive_representation.py
  dev/verify_phase_xc1.sh
  docs/architecture/cognitive_representation_architecture.md
)

for path in "${required[@]}"; do
    [[ -f "$path" ]] || { echo "[FAIL] Missing $path"; exit 1; }
done

chmod +x dev/verify_phase_xc1.sh dev/verification/verify_phase_xc1_cognitive_representation.py

"$PYTHON_BIN" -m compileall -q core/representation
"$PYTHON_BIN" -m unittest tests.test_phase_xc1_cognitive_representation
"$PYTHON_BIN" dev/verification/verify_phase_xc1_cognitive_representation.py
PYTHON_BIN="$PYTHON_BIN" ./dev/verify_phase_xc1.sh
