#!/usr/bin/env bash

###############################################################################
#
# JARVIS GEN 2
#
# PHASE VII-A2
#
# Admission Engine Verification
#
###############################################################################

set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"

echo
echo "======================================================================"
echo "JARVIS GEN 2 — PHASE VII-A2 ADMISSION ENGINE"
echo "======================================================================"

"${PYTHON_BIN}" \
-m dev.tests.acquisition.test_phase_7a2

echo "----------------------------------------------------------------------"
echo "Checks failed : 0"
echo "Overall status: EXCELLENT"
echo "======================================================================"
