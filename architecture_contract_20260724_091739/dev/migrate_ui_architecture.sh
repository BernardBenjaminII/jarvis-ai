#!/usr/bin/env bash

###############################################################################
# JARVIS Gen 2
# Mission Control Architecture Migration
#
# Moves the existing UI architecture into the canonical
# docs/architecture/ui hierarchy.
###############################################################################

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

OLD_DIR="${PROJECT_ROOT}/docs/ui"
NEW_ROOT="${PROJECT_ROOT}/docs/architecture"
NEW_DIR="${NEW_ROOT}/ui"

echo
echo "============================================================"
echo "JARVIS Mission Control Architecture Migration"
echo "============================================================"
echo

###############################################################################
# Verify source exists
###############################################################################

if [[ ! -d "${OLD_DIR}" ]]; then
    echo "ERROR: Source directory not found:"
    echo "  ${OLD_DIR}"
    exit 1
fi

###############################################################################
# Create destination hierarchy
###############################################################################

mkdir -p "${NEW_DIR}"

###############################################################################
# Move files
###############################################################################

echo "Moving architecture documents..."

find "${OLD_DIR}" \
    -maxdepth 1 \
    -type f \
    -exec mv {} "${NEW_DIR}" \;

###############################################################################
# Remove old directory if empty
###############################################################################

if [[ -z "$(ls -A "${OLD_DIR}")" ]]; then
    rmdir "${OLD_DIR}"
    echo "Removed empty directory:"
    echo "  ${OLD_DIR}"
fi

###############################################################################
# Summary
###############################################################################

echo
echo "Migration complete."
echo
echo "New architecture location:"
echo "  ${NEW_DIR}"
echo

echo "Contents:"
echo

find "${NEW_DIR}" \
    -maxdepth 1 \
    -type f \
    | sort

echo
echo "============================================================"
echo "Migration Complete"
echo "============================================================"
