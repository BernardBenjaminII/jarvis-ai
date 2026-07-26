#!/usr/bin/env bash
set -euo pipefail

# JARVIS — CONST-0001 Canonicalization Installer
#
# Purpose:
#   Perform the one-time structural migration required before ratification of
#   CONST-0001 Revision 1.0.
#
# Canonicalization actions:
#   1. Create a timestamped backup.
#   2. Move Article XIX so it immediately follows Article XVIII.
#   3. Preserve the first structured Certification Appendix.
#   4. Remove a later duplicate all-caps Certification Appendix section.
#   5. Remove consecutive duplicate "Every Article shall map..." statements.
#   6. Normalize line endings and excessive blank lines.
#   7. Verify Articles I–XIX exist exactly once and in canonical order.
#   8. Verify Article XIX precedes all appendices and final certification.
#   9. Produce a deterministic migration report.
#
# Usage:
#   ./dev/install_constitution_v1_canonicalization.sh
#
# Optional environment variables:
#   CONSTITUTION_FILE  Override canonical Constitution path.
#   PYTHON_BIN         Override Python interpreter.

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_ROOT"

CONSTITUTION_FILE="${CONSTITUTION_FILE:-docs/constitution/executive.md}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR=".migration_backups/constitution_v1_canonicalization_${TIMESTAMP}"
BACKUP_FILE="${BACKUP_DIR}/executive.md"
AUDIT_DIR="docs/audits"
REPORT_FILE="${AUDIT_DIR}/constitution_v1_canonicalization_report.md"

if [[ ! -f "$CONSTITUTION_FILE" ]]; then
    echo "ERROR: Constitution not found: $CONSTITUTION_FILE"
    exit 2
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "ERROR: Python interpreter not found: $PYTHON_BIN"
    exit 2
fi

mkdir -p "$BACKUP_DIR" "$AUDIT_DIR"
cp -a "$CONSTITUTION_FILE" "$BACKUP_FILE"

REPOSITORY_REVISION="$(git rev-parse HEAD 2>/dev/null || printf 'UNAVAILABLE')"
REPOSITORY_BRANCH="$(git branch --show-current 2>/dev/null || printf 'UNAVAILABLE')"

export CONSTITUTION_FILE
export BACKUP_FILE
export REPORT_FILE
export REPOSITORY_REVISION
export REPOSITORY_BRANCH
export TIMESTAMP

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import hashlib
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

constitution_path = Path(os.environ["CONSTITUTION_FILE"])
backup_file = os.environ["BACKUP_FILE"]
report_path = Path(os.environ["REPORT_FILE"])
repository_revision = os.environ["REPOSITORY_REVISION"]
repository_branch = os.environ["REPOSITORY_BRANCH"]

EXPECTED_ARTICLES = [
    "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
    "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX",
]

ARTICLE_PATTERN = re.compile(
    r"(?mi)^[ \t]*(?:#+[ \t]*)?ARTICLE[ \t]+"
    r"(XIX|XVIII|XVII|XVI|XV|XIV|XIII|XII|XI|X|IX|VIII|VII|VI|V|IV|III|II|I)"
    r"(?:[ \t]*(?:—|-).*)?[ \t]*$"
)

def fail(message: str) -> None:
    print(f"[FAIL] {message}", file=sys.stderr)
    raise SystemExit(1)

def sha256_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

def article_matches(text: str) -> list[re.Match[str]]:
    return list(ARTICLE_PATTERN.finditer(text))

def article_index(matches: list[re.Match[str]]) -> dict[str, list[int]]:
    result: dict[str, list[int]] = {article: [] for article in EXPECTED_ARTICLES}
    for match in matches:
        result[match.group(1).upper()].append(match.start())
    return result

def next_structural_boundary(
    text: str,
    start: int,
    patterns: list[re.Pattern[str]],
) -> int:
    candidates: list[int] = []
    for pattern in patterns:
        match = pattern.search(text, start)
        if match:
            candidates.append(match.start())
    return min(candidates) if candidates else len(text)

def remove_consecutive_mapping_duplicates(text: str) -> tuple[str, int]:
    sentence = (
        r"Every Article shall map to responsible packages,\s*"
        r"ADRs,\s*verification suites,\s*certification suites,\s*"
        r"and implementation modules\."
    )
    pattern = re.compile(rf"(?is)({sentence})\s*\n\s*\n\s*\1")
    removals = 0
    while True:
        updated, count = pattern.subn(r"\1", text)
        removals += count
        if count == 0:
            return text, removals
        text = updated

def remove_duplicate_all_caps_appendix(text: str) -> tuple[str, int]:
    """
    Remove only a later duplicate heading written exactly as:
        # CERTIFICATION APPENDIX

    Keep the structured:
        # Certification Appendix

    The duplicate block ends at the next major section heading among:
      - Constitutional Traceability
      - FINAL CONSTITUTIONAL CERTIFICATION
      - Executive Constitutional Covenant
      - Ratification
      - Article XIX
    """
    heading_pattern = re.compile(
        r"(?m)^[ \t]*#+[ \t]+CERTIFICATION APPENDIX[ \t]*$"
    )
    matches = list(heading_pattern.finditer(text))
    if not matches:
        return text, 0

    removed = 0
    for match in reversed(matches):
        boundary_patterns = [
            re.compile(r"(?mi)^[ \t]*#+[ \t]+Constitutional Traceability[ \t]*$"),
            re.compile(r"(?mi)^[ \t]*#+[ \t]+FINAL CONSTITUTIONAL CERTIFICATION[ \t]*$"),
            re.compile(r"(?mi)^[ \t]*(?:#+[ \t]*)?Executive Constitutional Covenant[ \t]*$"),
            re.compile(r"(?mi)^[ \t]*(?:#+[ \t]*)?Ratification[ \t]*$"),
            re.compile(r"(?mi)^[ \t]*(?:#+[ \t]*)?ARTICLE[ \t]+XIX(?:[ \t]*(?:—|-).*)?[ \t]*$"),
        ]
        end = next_structural_boundary(text, match.end(), boundary_patterns)
        text = text[:match.start()].rstrip() + "\n\n" + text[end:].lstrip()
        removed += 1

    return text, removed

def extract_article_xix(text: str) -> tuple[str, str]:
    matches = article_matches(text)
    xix_matches = [m for m in matches if m.group(1).upper() == "XIX"]

    if len(xix_matches) != 1:
        fail(f"Expected exactly one Article XIX heading; found {len(xix_matches)}.")

    start_match = xix_matches[0]
    start = start_match.start()

    # Article XIX normally runs to EOF in the pre-canonical draft. If any known
    # appendices or final constitutional sections follow it, stop there.
    boundary_patterns = [
        re.compile(r"(?mi)^[ \t]*#+[ \t]+Certification Appendix[ \t]*$"),
        re.compile(r"(?m)^[ \t]*#+[ \t]+CERTIFICATION APPENDIX[ \t]*$"),
        re.compile(r"(?mi)^[ \t]*#+[ \t]+Constitutional Traceability[ \t]*$"),
        re.compile(r"(?mi)^[ \t]*#+[ \t]+FINAL CONSTITUTIONAL CERTIFICATION[ \t]*$"),
        re.compile(r"(?mi)^[ \t]*(?:#+[ \t]*)?Executive Constitutional Covenant[ \t]*$"),
        re.compile(r"(?mi)^[ \t]*(?:#+[ \t]*)?Ratification[ \t]*$"),
    ]
    end = next_structural_boundary(text, start_match.end(), boundary_patterns)

    article_block = text[start:end].strip()
    remaining = text[:start].rstrip() + "\n\n" + text[end:].lstrip()
    return remaining, article_block

def find_article_end(text: str, article: str) -> int:
    matches = article_matches(text)
    target_index = None
    for index, match in enumerate(matches):
        if match.group(1).upper() == article:
            target_index = index
            break

    if target_index is None:
        fail(f"Article {article} heading not found.")

    if target_index + 1 < len(matches):
        return matches[target_index + 1].start()

    boundary_patterns = [
        re.compile(r"(?mi)^[ \t]*#+[ \t]+Certification Appendix[ \t]*$"),
        re.compile(r"(?m)^[ \t]*#+[ \t]+CERTIFICATION APPENDIX[ \t]*$"),
        re.compile(r"(?mi)^[ \t]*#+[ \t]+Constitutional Traceability[ \t]*$"),
        re.compile(r"(?mi)^[ \t]*#+[ \t]+FINAL CONSTITUTIONAL CERTIFICATION[ \t]*$"),
        re.compile(r"(?mi)^[ \t]*(?:#+[ \t]*)?Executive Constitutional Covenant[ \t]*$"),
        re.compile(r"(?mi)^[ \t]*(?:#+[ \t]*)?Ratification[ \t]*$"),
    ]
    target_match = matches[target_index]
    return next_structural_boundary(text, target_match.end(), boundary_patterns)

def insert_article_xix_after_xviii(text: str, article_xix: str) -> str:
    insert_at = find_article_end(text, "XVIII")
    return (
        text[:insert_at].rstrip()
        + "\n\n"
        + article_xix.strip()
        + "\n\n"
        + text[insert_at:].lstrip()
    )

def normalize_spacing(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.rstrip() + "\n"

original = constitution_path.read_text(encoding="utf-8")
working = original.replace("\r\n", "\n").replace("\r", "\n")

before_hash = sha256_text(working)

working, mapping_duplicate_removals = remove_consecutive_mapping_duplicates(working)
working, duplicate_appendix_removals = remove_duplicate_all_caps_appendix(working)

positions_before_move = article_index(article_matches(working))
missing_before_move = [a for a, values in positions_before_move.items() if not values]
duplicates_before_move = {
    a: len(values)
    for a, values in positions_before_move.items()
    if len(values) > 1
}

if missing_before_move:
    fail(
        "Cannot canonicalize because Articles are missing: "
        + ", ".join(missing_before_move)
    )

if duplicates_before_move:
    fail(
        "Cannot canonicalize because duplicate Article headings exist: "
        + ", ".join(
            f"{article}={count}"
            for article, count in duplicates_before_move.items()
        )
    )

article_xviii_position = positions_before_move["XVIII"][0]
article_xix_position = positions_before_move["XIX"][0]

moved_article_xix = article_xix_position < article_xviii_position

if article_xix_position > article_xviii_position:
    # Determine whether Article XIX is already directly after Article XVIII.
    ordered = [
        match.group(1).upper()
        for match in article_matches(working)
    ]
    xviii_index = ordered.index("XVIII")
    already_canonical = (
        xviii_index + 1 < len(ordered)
        and ordered[xviii_index + 1] == "XIX"
    )
else:
    already_canonical = False

if not already_canonical:
    working_without_xix, article_xix_block = extract_article_xix(working)
    working = insert_article_xix_after_xviii(
        working_without_xix,
        article_xix_block,
    )
    moved_article_xix = True

working = normalize_spacing(working)

matches_after = article_matches(working)
positions_after = article_index(matches_after)

missing_after = [a for a, values in positions_after.items() if not values]
duplicates_after = {
    a: len(values)
    for a, values in positions_after.items()
    if len(values) > 1
}

if missing_after:
    fail("Post-migration Articles missing: " + ", ".join(missing_after))

if duplicates_after:
    fail(
        "Post-migration duplicate Article headings: "
        + ", ".join(
            f"{article}={count}"
            for article, count in duplicates_after.items()
        )
    )

actual_order = [match.group(1).upper() for match in matches_after]
if actual_order != EXPECTED_ARTICLES:
    fail(
        "Articles are not in canonical order after migration.\n"
        f"Expected: {' '.join(EXPECTED_ARTICLES)}\n"
        f"Actual:   {' '.join(actual_order)}"
    )

structured_appendix_matches = list(
    re.finditer(r"(?mi)^[ \t]*#+[ \t]+Certification Appendix[ \t]*$", working)
)
all_caps_appendix_matches = list(
    re.finditer(r"(?m)^[ \t]*#+[ \t]+CERTIFICATION APPENDIX[ \t]*$", working)
)
traceability_matches = list(
    re.finditer(r"(?mi)^[ \t]*#+[ \t]+Constitutional Traceability[ \t]*$", working)
)
final_certification_matches = list(
    re.finditer(
        r"(?mi)^[ \t]*#+[ \t]+FINAL CONSTITUTIONAL CERTIFICATION[ \t]*$",
        working,
    )
)
ratification_matches = list(
    re.finditer(r"(?mi)^[ \t]*(?:#+[ \t]*)?Ratification[ \t]*$", working)
)

if len(structured_appendix_matches) != 1:
    fail(
        "Expected exactly one structured Certification Appendix; "
        f"found {len(structured_appendix_matches)}."
    )

if all_caps_appendix_matches:
    fail(
        "Duplicate all-caps Certification Appendix remains after migration."
    )

if len(traceability_matches) != 1:
    fail(
        "Expected exactly one Constitutional Traceability section; "
        f"found {len(traceability_matches)}."
    )

if len(final_certification_matches) != 1:
    fail(
        "Expected exactly one Final Constitutional Certification section; "
        f"found {len(final_certification_matches)}."
    )

if len(ratification_matches) != 1:
    fail(
        "Expected exactly one Ratification heading; "
        f"found {len(ratification_matches)}."
    )

xix_position = positions_after["XIX"][0]
appendix_position = structured_appendix_matches[0].start()
traceability_position = traceability_matches[0].start()
final_certification_position = final_certification_matches[0].start()
ratification_position = ratification_matches[0].start()

if not (
    xix_position
    < appendix_position
    < traceability_position
    < final_certification_position
    < ratification_position
):
    fail(
        "Canonical section order is invalid. Required order:\n"
        "Article XIX → Certification Appendix → Constitutional Traceability "
        "→ Final Constitutional Certification → Ratification"
    )

mapping_sentence_pattern = re.compile(
    r"(?is)Every Article shall map to responsible packages,\s*"
    r"ADRs,\s*verification suites,\s*certification suites,\s*"
    r"and implementation modules\."
)
mapping_occurrences = len(mapping_sentence_pattern.findall(working))
if mapping_occurrences > 1:
    fail(
        "Duplicate 'Every Article shall map...' statements remain: "
        f"{mapping_occurrences}"
    )

after_hash = sha256_text(working)
constitution_path.write_text(working, encoding="utf-8", newline="\n")

migration_time = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

report = f"""# CONST-0001 Canonicalization Report

**Result:** PASS  
**Document:** `{constitution_path.as_posix()}`  
**Document ID:** `CONST-0001`  
**Migration Date:** `{migration_time}`  
**Repository Revision:** `{repository_revision}`  
**Repository Branch:** `{repository_branch}`  
**Backup:** `{backup_file}`  
**Installer:** `dev/install_constitution_v1_canonicalization.sh`

## Migration Actions

- Article XIX moved after Article XVIII: {"YES" if moved_article_xix else "ALREADY CANONICAL"}
- Duplicate mapping statements removed: {mapping_duplicate_removals}
- Duplicate all-caps Certification Appendices removed: {duplicate_appendix_removals}
- Line endings normalized: PASS
- Excessive blank lines normalized: PASS

## Structural Verification

- Articles I–XIX present exactly once: PASS
- Articles I–XIX in canonical order: PASS
- Article XIX precedes appendices: PASS
- Structured Certification Appendix unique: PASS
- All-caps duplicate Certification Appendix absent: PASS
- Constitutional Traceability unique: PASS
- Final Constitutional Certification unique: PASS
- Ratification heading unique: PASS
- Canonical section order valid: PASS
- UTF-8 serialization: PASS

## Content Fingerprints

**Before canonicalization**

```text
{before_hash}
```

**After canonicalization**

```text
{after_hash}
```
"""

report_path.write_text(report, encoding="utf-8", newline="\n")

print("[PASS] Timestamped backup created")
print("[PASS] Article XIX placed after Article XVIII")
print("[PASS] Duplicate mapping statement cleanup complete")
print("[PASS] Duplicate Certification Appendix cleanup complete")
print("[PASS] Articles I–XIX present exactly once")
print("[PASS] Articles I–XIX in canonical order")
print("[PASS] Canonical appendix and ratification order verified")
print("[PASS] Constitution written as UTF-8")
print(f"[PASS] Migration report: {report_path}")
print(f"[PASS] Canonical SHA-256: {after_hash}")
PY

echo
echo "========================================================================"
echo "JARVIS — CONST-0001 CANONICALIZATION"
echo "========================================================================"
echo "[PASS] Canonicalization completed"
echo "[PASS] Constitution : $CONSTITUTION_FILE"
echo "[PASS] Backup       : $BACKUP_FILE"
echo "[PASS] Audit report : $REPORT_FILE"
echo "[PASS] Git revision : $REPOSITORY_REVISION"
echo "[PASS] Git branch   : $REPOSITORY_BRANCH"
echo "------------------------------------------------------------------------"
echo "Next:"
echo "  ./dev/ratify_constitution_v1.sh \"Bernard Benjamin II\""
echo "------------------------------------------------------------------------"
echo "Overall status: EXCELLENT"
echo "========================================================================"
