#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
cd "$PROJECT_ROOT"
"$PYTHON_BIN" dev/verification/verify_convergence_c4.py
"$PYTHON_BIN" -m unittest \
  tests.test_convergence_c1_executive_conversation \
  tests.test_convergence_c1_http_contract \
  tests.test_convergence_c2_director_activation \
  tests.test_convergence_c2_http_contract \
  tests.test_convergence_c2a_certification_repair \
  tests.test_convergence_c3_capability_routing \
  tests.test_convergence_c4_knowledge_grounding
printf '[PASS] C-1 through C-4 deterministic tests\n'
