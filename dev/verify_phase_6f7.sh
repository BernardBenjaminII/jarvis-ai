#!/usr/bin/env bash

set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"

printf '\n'
printf '%s\n' '======================================================================'
printf '%s\n' 'JARVIS GEN 2 — PHASE VI-F7 DEVELOPER INFRASTRUCTURE'
printf '%s\n' '======================================================================'

"${PYTHON_BIN}" -m py_compile \
    dev/release/__init__.py \
    dev/release/safe_commit.py \
    dev/tests/test_safe_commit.py \
    dev/verification/registry.py \
    dev/tests/test_verification_framework.py

bash -n dev/safe_commit.sh

"${PYTHON_BIN}" -m dev.tests.test_safe_commit
"${PYTHON_BIN}" -m dev.tests.test_verification_framework

"${PYTHON_BIN}" -m dev.verification.runner \
    --list \
    | grep -q '6f7'

if [[ ! -s .github/workflows/jarvis-verification.yml ]]; then
    printf '%s\n' \
        'Missing GitHub Actions verification workflow.' >&2
    exit 1
fi

if [[ ! -s \
docs/architecture/milestones/phase_vi_f7_developer_infrastructure.md ]]
then
    printf '%s\n' \
        'Missing VI-F7 milestone documentation.' >&2
    exit 1
fi

printf '%s\n' '[PASS] Safe-commit implementation'
printf '%s\n' '[PASS] Safe-commit contract tests'
printf '%s\n' '[PASS] Verification framework contracts'
printf '%s\n' '[PASS] GitHub Actions workflow present'
printf '%s\n' '[PASS] VI-F7 registered'
printf '%s\n' '[PASS] VI-F7 milestone documentation present'
printf '%s\n' '----------------------------------------------------------------------'
printf '%s\n' 'Checks failed : 0'
printf '%s\n' 'Overall status: EXCELLENT'
printf '%s\n' '======================================================================'
