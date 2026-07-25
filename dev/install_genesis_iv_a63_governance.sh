#!/usr/bin/env bash
#
# ============================================================
# JARVIS
# Genesis IV-A6.3 Governance Installer
#
# Installs:
#   • Executive Constitution
#   • ADR-0033 Executive COA Evaluation Policy
#   • IV-A6.3 Architecture Specification
#
# Safe:
#   • Creates timestamped backup
#   • Refuses invalid archives
#   • Preserves permissions
# ============================================================

set -Eeuo pipefail

ARCHIVE="${1:-genesis_iv_a63_governance.zip}"
PROJECT_ROOT="$(pwd)"

BACKUP_ROOT=".migration_backups/genesis_iv_a63_governance_$(date +%Y%m%d_%H%M%S)"

echo
echo "============================================================"
echo "Genesis IV-A6.3 Governance Installer"
echo "============================================================"
echo

if [[ ! -f "$ARCHIVE" ]]; then
    echo "[FAIL] Archive not found:"
    echo "       $ARCHIVE"
    exit 1
fi

if [[ ! -d docs ]]; then
    echo "[FAIL] This script must be run from the repository root."
    exit 1
fi

echo "[PASS] Archive located"
echo "[PASS] Repository root verified"

mkdir -p "$BACKUP_ROOT"

echo
echo "Creating backup..."

backup_if_exists () {

    local FILE="$1"

    if [[ -f "$FILE" ]]; then

        mkdir -p "$BACKUP_ROOT/$(dirname "$FILE")"

        cp "$FILE" "$BACKUP_ROOT/$FILE"

        echo "  backed up $FILE"

    fi

}

backup_if_exists docs/constitution/executive.md
backup_if_exists docs/decisions/ADR-0033-executive-course-of-action-evaluation-policy.md
backup_if_exists docs/architecture/genesis_iv_a63_executive_course_of_action_evaluation.md

TMPDIR="$(mktemp -d)"

cleanup() {
    rm -rf "$TMPDIR"
}

trap cleanup EXIT

echo
echo "Extracting package..."

unzip -q "$ARCHIVE" -d "$TMPDIR"

PACKAGE="$(find "$TMPDIR" -maxdepth 1 -type d -name "genesis_iv_a63_governance*" | head -1)"

if [[ -z "$PACKAGE" ]]; then
    echo "[FAIL] Invalid package."
    exit 1
fi

echo "[PASS] Package extracted"

echo
echo "Installing..."

mkdir -p docs/constitution
mkdir -p docs/decisions
mkdir -p docs/architecture

cp \
"$PACKAGE/docs/constitution/executive.md" \
docs/constitution/

cp \
"$PACKAGE/docs/decisions/ADR-0033-executive-course-of-action-evaluation-policy.md" \
docs/decisions/

cp \
"$PACKAGE/docs/architecture/genesis_iv_a63_executive_course_of_action_evaluation.md" \
docs/architecture/

echo "[PASS] Executive Constitution"
echo "[PASS] ADR-0033"
echo "[PASS] Architecture Specification"

echo
echo "============================================================"
echo "Genesis IV-A6.3 Governance Installed"
echo "============================================================"
echo
echo "Backup:"
echo "    $BACKUP_ROOT"
echo
