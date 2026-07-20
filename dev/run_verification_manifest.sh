#!/usr/bin/env bash

###############################################################################
#
# JARVIS GEN 2
#
# Deterministic Verification Manifest Runner
#
# Executes verifier paths listed in a manifest, in declared order.
#
###############################################################################

set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"
export PYTHON_BIN

if [[ "$#" -ne 2 ]]; then
    echo "Usage: $0 <domain-name> <manifest-path>" >&2
    exit 2
fi

DOMAIN_NAME="$1"
MANIFEST_PATH="$2"

if [[ ! -f "${MANIFEST_PATH}" ]]; then
    echo "[FAIL] Verification manifest not found: ${MANIFEST_PATH}" >&2
    exit 1
fi

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

echo
echo "======================================================================"
echo "JARVIS GEN 2 — ${DOMAIN_NAME} VERIFICATION SUITE"
echo "======================================================================"

while IFS= read -r raw_line || [[ -n "${raw_line}" ]]; do
    line="${raw_line#"${raw_line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"

    [[ -z "${line}" ]] && continue
    [[ "${line}" == \#* ]] && continue

    if [[ "${line}" == /* ]]; then
        echo "[FAIL] Manifest entries must be repository-relative: ${line}"
        FAILED=$((FAILED + 1))
        continue
    fi

    if [[ "${line}" == *".."* ]]; then
        echo "[FAIL] Manifest entries may not traverse directories: ${line}"
        FAILED=$((FAILED + 1))
        continue
    fi

    run_suite "${line}"
done < "${MANIFEST_PATH}"

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo
echo "======================================================================"
echo "${DOMAIN_NAME} VERIFICATION SUMMARY"
echo "======================================================================"

printf "%-24s %6d\n" "Suites Executed:" "${TOTAL}"
printf "%-24s %6d\n" "Suites Passed:" "${PASSED}"
printf "%-24s %6d\n" "Suites Failed:" "${FAILED}"
printf "%-24s %6d sec\n" "Elapsed Time:" "${ELAPSED}"

echo

if [[ "${FAILED}" -eq 0 ]]; then
    echo "Overall Status : EXCELLENT"
    exit 0
fi

echo "Overall Status : FAILED"
exit 1
