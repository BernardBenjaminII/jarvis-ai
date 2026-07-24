#!/usr/bin/env bash

###############################################################################
#
# JARVIS GEN 2
#
# Master Verification Suite
#
# Stable public verification entry point.
# Delegates verification to architectural domain orchestrators.
#
###############################################################################

set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"
export PYTHON_BIN

echo
echo "======================================================================"
echo "JARVIS GEN 2 — MASTER VERIFICATION SUITE"
echo "======================================================================"

START_TIME=$(date +%s)

TOTAL=0
PASSED=0
FAILED=0

run_domain() {
    local script="$1"

    TOTAL=$((TOTAL + 1))

    echo
    echo "----------------------------------------------------------------------"
    echo "Running domain orchestrator ${script}"
    echo "----------------------------------------------------------------------"

    if [[ ! -f "${script}" ]]; then
        echo "[FAIL] ${script} (missing)"
        FAILED=$((FAILED + 1))
        return
    fi

    if [[ ! -x "${script}" ]]; then
        echo "[FAIL] ${script} (not executable)"
        FAILED=$((FAILED + 1))
        return
    fi

    if "${script}"; then
        PASSED=$((PASSED + 1))
        echo
        echo "[PASS] ${script}"
    else
        FAILED=$((FAILED + 1))
        echo
        echo "[FAIL] ${script}"
    fi
}

###############################################################################
# Verification Domains
###############################################################################

run_domain ./dev/verify_knowledge_all.sh
run_domain ./dev/verify_genesis_all.sh

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo
echo "======================================================================"
echo "MASTER VERIFICATION SUMMARY"
echo "======================================================================"

printf "%-24s %6d\n" "Domains Executed:" "${TOTAL}"
printf "%-24s %6d\n" "Domains Passed:" "${PASSED}"
printf "%-24s %6d\n" "Domains Failed:" "${FAILED}"
printf "%-24s %6d sec\n" "Elapsed Time:" "${ELAPSED}"

echo

if [[ "${FAILED}" -eq 0 ]]; then
    echo "Overall Status : EXCELLENT"
    echo
    echo "JARVIS Gen 2 verification PASSED."
    exit 0
fi

echo "Overall Status : FAILED"
echo
echo "One or more verification domains failed."
exit 1
