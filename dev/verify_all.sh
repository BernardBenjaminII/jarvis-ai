#!/usr/bin/env bash

###############################################################################
#
# JARVIS GEN 2
#
# Master Verification Suite
#
# Executes every available verification suite in dependency order.
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

run_suite() {

    local script="$1"

    TOTAL=$((TOTAL + 1))

    echo
    echo "----------------------------------------------------------------------"
    echo "Running ${script}"
    echo "----------------------------------------------------------------------"

    if [[ ! -x "${script}" ]]; then
        echo "[SKIP] ${script} (not found or not executable)"
        FAILED=$((FAILED + 1))
        return
    fi

    if "${script}"
    then
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
# Assimilation
###############################################################################

run_suite ./dev/verify_phase_6b.sh
run_suite ./dev/verify_phase_6c.sh

###############################################################################
# Future phases
###############################################################################

 run_suite ./dev/verify_phase_6d0.sh
 run_suite ./dev/verify_phase_6d1.sh
 run_suite ./dev/verify_phase_6d2.sh
run_suite ./dev/verify_phase_6e1.sh
run_suite ./dev/verify_phase_6e2.sh
run_suite ./dev/verify_phase_6e3.sh

###############################################################################
# Future subsystems
###############################################################################

# run_suite ./dev/verify_search.sh
# run_suite ./dev/verify_embeddings.sh
# run_suite ./dev/verify_director.sh
# run_suite ./dev/verify_agents.sh
# run_suite ./dev/verify_memory.sh
# run_suite ./dev/verify_security.sh
# run_suite ./dev/verify_recon.sh

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo
echo "======================================================================"
echo "MASTER VERIFICATION SUMMARY"
echo "======================================================================"

printf "%-24s %6d\n" "Suites Executed:" "${TOTAL}"
printf "%-24s %6d\n" "Suites Passed:"   "${PASSED}"
printf "%-24s %6d\n" "Suites Failed:"   "${FAILED}"
printf "%-24s %6d sec\n" "Elapsed Time:" "${ELAPSED}"

echo

if [[ "${FAILED}" -eq 0 ]]
then
    echo "Overall Status : EXCELLENT"
    echo
    echo "JARVIS Gen 2 verification PASSED."
    exit 0
else
    echo "Overall Status : FAILED"
    echo
    echo "One or more verification suites failed."
    exit 1
fi
