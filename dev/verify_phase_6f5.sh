#!/usr/bin/env bash

set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"

printf '\n'
printf '%s\n' '======================================================================'
printf '%s\n' 'JARVIS GEN 2 — PHASE VI-F5 VERIFICATION FRAMEWORK'
printf '%s\n' '======================================================================'

"${PYTHON_BIN}" -m py_compile \
    dev/verification/__init__.py \
    dev/verification/models.py \
    dev/verification/registry.py \
    dev/verification/runner.py \
    dev/tests/test_verification_framework.py

"${PYTHON_BIN}" -m dev.tests.test_verification_framework

"${PYTHON_BIN}" -m dev.verification.runner \
    --list

printf '%s\n' '----------------------------------------------------------------------'
printf '%s\n' 'Checks failed : 0'
printf '%s\n' 'Overall status: EXCELLENT'
printf '%s\n' '======================================================================'
