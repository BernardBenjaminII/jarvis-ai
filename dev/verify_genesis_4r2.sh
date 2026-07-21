#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$PROJECT_ROOT"

printf '\n======================================================================\n'
printf 'JARVIS GENESIS IV-R2 — OBSERVATION ENGINE CERTIFICATION\n'
printf '======================================================================\n\n'

"$PYTHON_BIN" -m compileall -q \
  core/cognition/common \
  core/cognition/layers/observation

"$PYTHON_BIN" dev/verification/verify_genesis_4r2_observation_engine.py

printf '\n======================================================================\n'
printf 'GENESIS IV-R2 CERTIFICATION COMPLETE\n'
printf '======================================================================\n\n'
