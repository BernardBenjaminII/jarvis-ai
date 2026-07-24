#!/usr/bin/env bash
#
# ============================================================
# JARVIS
# Architecture Contract Extractor
#
# Produces a deterministic snapshot of the current architecture
# suitable for certification, migration, auditing, and AI repair.
# ============================================================

set -Eeuo pipefail

ROOT="${PROJECT_ROOT:-$(pwd)}"
cd "$ROOT"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

OUTPUT_DIR="artifacts/architecture_contract_${TIMESTAMP}"
ARCHIVE="${OUTPUT_DIR}.tar.gz"

mkdir -p "$OUTPUT_DIR"

echo
echo "============================================================"
echo "JARVIS ARCHITECTURE CONTRACT EXTRACTION"
echo "============================================================"
echo

###############################################################
# helper
###############################################################

copy_if_exists() {

    local file="$1"

    if [[ -f "$file" ]]; then

        mkdir -p "$OUTPUT_DIR/$(dirname "$file")"

        cp "$file" \
           "$OUTPUT_DIR/$file"

        echo "[PASS] $file"

    else

        echo "[MISS] $file"

    fi

}

###############################################################
# canonical directories
###############################################################

DIRECTORIES=(

core

tests

dev/verification

docs/architecture

docs/decisions

config

)

###############################################################
# inventories
###############################################################

mkdir -p "$OUTPUT_DIR/inventory"

echo
echo "Generating inventories..."

find core \
    -type f \
    | sort \
    > "$OUTPUT_DIR/inventory/core_files.txt"

find tests \
    -type f \
    | sort \
    > "$OUTPUT_DIR/inventory/test_files.txt"

find dev/verification \
    -type f \
    | sort \
    > "$OUTPUT_DIR/inventory/verification_files.txt"

###############################################################
# route inventory
###############################################################

grep -R \
    -nE '@(router|app)\.(get|post|put|delete|patch)' \
    core \
    > "$OUTPUT_DIR/inventory/routes.txt" \
    || true

###############################################################
# FastAPI paths
###############################################################

grep -R \
    -nE '"/[^"]+"' \
    core/src/routes \
    > "$OUTPUT_DIR/inventory/path_literals.txt" \
    || true

###############################################################
# public exports
###############################################################

grep -R \
    -n "__all__" \
    core \
    > "$OUTPUT_DIR/inventory/public_exports.txt" \
    || true

###############################################################
# dataclasses
###############################################################

grep -R \
    -n "@dataclass" \
    core \
    > "$OUTPUT_DIR/inventory/dataclasses.txt" \
    || true

###############################################################
# enums
###############################################################

grep -R \
    -n "Enum" \
    core \
    > "$OUTPUT_DIR/inventory/enums.txt" \
    || true

###############################################################
# projections
###############################################################

grep -R \
    -ni "projection" \
    core \
    > "$OUTPUT_DIR/inventory/projections.txt" \
    || true

###############################################################
# bridge
###############################################################

grep -R \
    -ni "bridge" \
    core \
    > "$OUTPUT_DIR/inventory/bridge.txt" \
    || true

###############################################################
# capability
###############################################################

grep -R \
    -ni "capabilit" \
    core \
    > "$OUTPUT_DIR/inventory/capabilities.txt" \
    || true

###############################################################
# imports
###############################################################

grep -R \
    -n "^from " \
    core \
    > "$OUTPUT_DIR/inventory/imports.txt" \
    || true

###############################################################
# architecture docs
###############################################################

echo
echo "Copying architecture..."

find docs \
    \( \
        -path "*/architecture/*" \
        -o \
        -path "*/decisions/*" \
    \) \
    -type f \
| while read file
do
    copy_if_exists "$file"
done

###############################################################
# config
###############################################################

echo
echo "Copying configuration..."

find config \
    -type f \
| while read file
do
    copy_if_exists "$file"
done

###############################################################
# verification
###############################################################

echo
echo "Copying verification..."

find dev/verification \
    -type f \
| while read file
do
    copy_if_exists "$file"
done

###############################################################
# tests
###############################################################

echo
echo "Copying tests..."

find tests \
    -type f \
| while read file
do
    copy_if_exists "$file"
done

###############################################################
# core
###############################################################

echo
echo "Copying source..."

find core \
    -type f \
| while read file
do
    copy_if_exists "$file"
done

###############################################################
# git information
###############################################################

echo
echo "Collecting git metadata..."

git rev-parse HEAD \
    > "$OUTPUT_DIR/git_commit.txt" \
    2>/dev/null \
    || true

git branch \
    > "$OUTPUT_DIR/git_branch.txt" \
    2>/dev/null \
    || true

git status \
    > "$OUTPUT_DIR/git_status.txt" \
    2>/dev/null \
    || true

###############################################################
# fingerprints
###############################################################

echo
echo "Generating SHA256 inventory..."

find "$OUTPUT_DIR" \
    -type f \
    ! -name sha256.txt \
| sort \
| while read file
do
    sha256sum "$file"
done \
> "$OUTPUT_DIR/sha256.txt"

###############################################################
# archive
###############################################################

echo
echo "Creating archive..."

tar -czf "$ARCHIVE" \
    -C artifacts \
    "$(basename "$OUTPUT_DIR")"

echo
echo "============================================================"
echo "COMPLETE"
echo "============================================================"
echo
echo "Output directory:"
echo "    $OUTPUT_DIR"
echo
echo "Archive:"
echo "    $ARCHIVE"
echo
echo "============================================================"
