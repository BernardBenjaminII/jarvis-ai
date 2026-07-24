#!/usr/bin/env bash

set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"

printf '\n'
printf '%s\n' '======================================================================'
printf '%s\n' 'JARVIS GEN 2 — PHASE VI-C PERSISTENT MISSION VERIFICATION'
printf '%s\n' '======================================================================'

"${PYTHON_BIN}" -m py_compile \
    knowledge_engine/assimilation/__init__.py \
    knowledge_engine/assimilation/schema.py \
    knowledge_engine/assimilation/dispatch.py \
    knowledge_engine/assimilation/mission.py \
    knowledge_engine/assimilation/mission_store.py \
    knowledge_engine/assimilation/planner.py \
    knowledge_engine/assimilation/director.py \
    knowledge_engine/assimilation/runner.py \
    knowledge_engine/assimilation/single_document.py \
    knowledge_engine/assimilation_cli.py \
    dev/tests/test_phase_6c.py

"${PYTHON_BIN}" -m dev.tests.test_phase_6c

printf '%s\n' '----------------------------------------------------------------------'
printf '%s\n' 'Checks failed : 0'
printf '%s\n' 'Overall status: EXCELLENT'
printf '%s\n' '======================================================================'
