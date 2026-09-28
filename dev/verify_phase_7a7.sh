#!/usr/bin/env bash

###############################################################################
#
# JARVIS GEN 2
#
# Phase VII-A7 Verification
#
# Canonical Assimilation Dispatch
#
###############################################################################

set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"

echo
echo "======================================================================"
echo "JARVIS GEN 2 — PHASE VII-A7 ASSIMILATION DISPATCH"
echo "======================================================================"

CHECKS_FAILED=0

run_test() {

    local module="$1"

    if ! "${PYTHON_BIN}" -m "${module}"
    then
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
}

###############################################################################
# Behaviour verification
###############################################################################

run_test dev.tests.acquisition.test_phase_7a7

###############################################################################
# Architecture verification
###############################################################################

run_test dev.tests.acquisition.test_phase_7a7_architecture

echo
echo "----------------------------------------------------------------------"

if [[ "${CHECKS_FAILED}" -eq 0 ]]
then
    echo "[PASS] Phase VII-A7 assimilation dispatch verified"
else
    echo "[FAIL] Phase VII-A7 assimilation dispatch verification"
fi

echo "----------------------------------------------------------------------"
echo "Checks failed : ${CHECKS_FAILED}"

if [[ "${CHECKS_FAILED}" -eq 0 ]]
then
    echo "Overall status: EXCELLENT"
else
    echo "Overall status: FAILED"
fi

echo "======================================================================"

exit "${CHECKS_FAILED}"
