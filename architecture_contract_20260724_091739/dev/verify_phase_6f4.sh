#!/usr/bin/env bash

set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"

printf '\n'
printf '%s\n' '======================================================================'
printf '%s\n' 'JARVIS GEN 2 — PHASE VI-F4 DETERMINISM AND PERFORMANCE'
printf '%s\n' '======================================================================'

"${PYTHON_BIN}" -m py_compile \
    knowledge_engine/assimilation/collection_plan.py \
    knowledge_engine/assimilation/runner.py \
    knowledge_engine/assimilation/repositories/knowledge_registry.py \
    knowledge_engine/assimilation/services/attempts.py \
    knowledge_engine/assimilation/services/extraction.py \
    knowledge_engine/assimilation/services/persistence.py \
    knowledge_engine/assimilation/services/state.py \
    dev/tests/test_performance_contracts.py

"${PYTHON_BIN}" -m dev.tests.test_performance_contracts

printf '%s\n' '----------------------------------------------------------------------'
printf '%s\n' 'Checks failed : 0'
printf '%s\n' 'Overall status: EXCELLENT'
printf '%s\n' '======================================================================'
