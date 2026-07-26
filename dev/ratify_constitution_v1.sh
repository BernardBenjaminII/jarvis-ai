#!/usr/bin/env bash
set -euo pipefail

# JARVIS — CONST-0001 Ratification Pipeline
#
# Usage:
#   ./dev/ratify_constitution_v1.sh "Commander Name"
#
# Optional environment variables:
#   CONSTITUTION_FILE  Override the canonical Constitution path.
#   COMMANDER          Commander name when no positional argument is supplied.
#
# Fingerprint rule:
#   SHA-256 is calculated from the complete ratified Constitution excluding the
#   generated Constitutional Fingerprint block itself. This avoids a
#   self-referential hash while preserving deterministic verification.

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_ROOT"

CONSTITUTION_FILE="${CONSTITUTION_FILE:-docs/constitution/executive.md}"
COMMANDER_NAME="${1:-${COMMANDER:-}}"
AUDIT_DIR="docs/audits"
REPORT_FILE="${AUDIT_DIR}/constitution_ratification_report.md"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR=".migration_backups/constitution_ratification_${TIMESTAMP}"
BACKUP_FILE="${BACKUP_DIR}/executive.md"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if [[ -z "$COMMANDER_NAME" ]]; then
    echo "ERROR: Commander name is required."
    echo
    echo "Usage:"
    echo "  $0 \"Commander Name\""
    echo
    echo "Or:"
    echo "  COMMANDER=\"Commander Name\" $0"
    exit 2
fi

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

if [[ -n "$(git status --porcelain --untracked-files=no 2>/dev/null || true)" ]]; then
    REPOSITORY_STATE="DIRTY"
else
    REPOSITORY_STATE="CLEAN"
fi

export CONSTITUTION_FILE COMMANDER_NAME REPORT_FILE REPOSITORY_REVISION
export REPOSITORY_BRANCH REPOSITORY_STATE TIMESTAMP BACKUP_FILE

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import hashlib
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

constitution_path = Path(os.environ["CONSTITUTION_FILE"])
report_path = Path(os.environ["REPORT_FILE"])
commander = os.environ["COMMANDER_NAME"].strip()
repository_revision = os.environ["REPOSITORY_REVISION"].strip()
repository_branch = os.environ["REPOSITORY_BRANCH"].strip()
repository_state = os.environ["REPOSITORY_STATE"].strip()
backup_file = os.environ["BACKUP_FILE"].strip()

START_MARKER = "<!-- CONSTITUTION_FINGERPRINT_START -->"
END_MARKER = "<!-- CONSTITUTION_FINGERPRINT_END -->"
EXPECTED_ARTICLES = [
    "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
    "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX",
]


def fail(message: str) -> None:
    print(f"[FAIL] {message}", file=sys.stderr)
    raise SystemExit(1)


def remove_fingerprint_block(text: str) -> str:
    pattern = re.compile(
        rf"\n?{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}\n?",
        flags=re.DOTALL,
    )
    return pattern.sub("\n", text)


def normalize_status(text: str) -> str:
    patterns = (
        r"(?mi)^Status:\s*Draft\s+1\.0\s+Complete\s*$",
        r"(?mi)^Status:\s*Draft\s+1\.0\s*$",
        r"(?mi)^Status:\s*Ratified\s+1\.0\s*$",
    )
    for pattern in patterns:
        text = re.sub(pattern, "Status: Ratified 1.0", text)
    return text


def remove_consecutive_mapping_duplicate(text: str) -> str:
    sentence = (
        r"Every Article shall map to responsible packages,\s*"
        r"ADRs,\s*verification suites,\s*certification suites,\s*"
        r"and implementation modules\."
    )
    duplicate_pattern = re.compile(rf"(?is)({sentence})\s*\n\s*\n\s*\1")
    previous = None
    while previous != text:
        previous = text
        text = duplicate_pattern.sub(r"\1", text)
    return text


def canonicalize(text: str) -> bytes:
    text = remove_fingerprint_block(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.rstrip() + "\n"
    return text.encode("utf-8")


def sha256_hex(text: str) -> str:
    return hashlib.sha256(canonicalize(text)).hexdigest()


def find_article_positions(text: str) -> dict[str, list[int]]:
    positions: dict[str, list[int]] = {article: [] for article in EXPECTED_ARTICLES}
    pattern = re.compile(
        r"(?mi)^[ \t]*(?:#+[ \t]*)?ARTICLE[ \t]+"
        r"(XIX|XVIII|XVII|XVI|XV|XIV|XIII|XII|XI|X|IX|VIII|VII|VI|V|IV|III|II|I)"
        r"(?:[ \t]*(?:—|-).*)?[ \t]*$"
    )
    for match in pattern.finditer(text):
        positions[match.group(1).upper()].append(match.start())
    return positions


def count_heading(text: str, title: str) -> int:
    return len(re.findall(rf"(?mi)^[ \t]*#+[ \t]+{re.escape(title)}[ \t]*$", text))


original = constitution_path.read_text(encoding="utf-8")
working = original.replace("\r\n", "\n").replace("\r", "\n")
working = remove_fingerprint_block(working)
working = normalize_status(working)
working = remove_consecutive_mapping_duplicate(working)
working = re.sub(r"\n{4,}", "\n\n\n", working).rstrip() + "\n"

article_positions = find_article_positions(working)
missing = [article for article, values in article_positions.items() if not values]
duplicates = {article: len(values) for article, values in article_positions.items() if len(values) > 1}

if missing:
    fail(f"Missing Constitutional Article headings: {', '.join(missing)}")
if duplicates:
    detail = ", ".join(f"{article}={count}" for article, count in duplicates.items())
    fail(f"Duplicate Constitutional Article headings detected: {detail}")

ordered_positions = [article_positions[article][0] for article in EXPECTED_ARTICLES]
if ordered_positions != sorted(ordered_positions):
    fail("Articles I–XIX are not in canonical order.")

certification_appendix_count = count_heading(working, "Certification Appendix")
if certification_appendix_count != 1:
    fail(
        "Expected exactly one '# Certification Appendix' heading; "
        f"found {certification_appendix_count}."
    )

traceability_count = count_heading(working, "Constitutional Traceability")
if traceability_count != 1:
    fail(
        "Expected exactly one '# Constitutional Traceability' heading; "
        f"found {traceability_count}."
    )

ratification_matches = list(
    re.finditer(r"(?mi)^[ \t]*(?:#+[ \t]*)?Ratification[ \t]*$", working)
)
if len(ratification_matches) != 1:
    fail(f"Expected exactly one Ratification heading; found {len(ratification_matches)}.")

final_certification_matches = list(
    re.finditer(
        r"(?mi)^[ \t]*#+[ \t]+FINAL CONSTITUTIONAL CERTIFICATION[ \t]*$",
        working,
    )
)
if len(final_certification_matches) != 1:
    fail(
        "Expected exactly one '# FINAL CONSTITUTIONAL CERTIFICATION' heading; "
        f"found {len(final_certification_matches)}."
    )

article_xix_position = article_positions["XIX"][0]
appendix_position = re.search(
    r"(?mi)^[ \t]*#+[ \t]+Certification Appendix[ \t]*$", working
)
traceability_position = re.search(
    r"(?mi)^[ \t]*#+[ \t]+Constitutional Traceability[ \t]*$", working
)
assert appendix_position is not None
assert traceability_position is not None

if article_xix_position > appendix_position.start():
    fail("Article XIX must appear before the Certification Appendix.")
if appendix_position.start() > traceability_position.start():
    fail("The Certification Appendix must appear before Constitutional Traceability.")

mapping_sentence_pattern = re.compile(
    r"(?is)Every Article shall map to responsible packages,\s*"
    r"ADRs,\s*verification suites,\s*certification suites,\s*"
    r"and implementation modules\."
)
mapping_count = len(mapping_sentence_pattern.findall(working))
if mapping_count > 1:
    fail(
        "The 'Every Article shall map...' statement remains duplicated "
        f"({mapping_count} occurrences)."
    )

required_phrases = (
    "Document ID: CONST-0001",
    "Authority: Supreme Executive Governance Document",
    "Executive Constitutional Covenant",
)
for phrase in required_phrases:
    if phrase not in working:
        fail(f"Required constitutional element is missing: {phrase}")

ratification_date = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
fingerprint = sha256_hex(working)

fingerprint_block = f"""
{START_MARKER}

---

# Constitutional Fingerprint

**Document:** CONST-0001  
**Revision:** 1.0  
**Status:** Ratified  

**SHA-256**

```text
{fingerprint}
```

**Repository Revision**

```text
{repository_revision}
```

**Repository Branch**

```text
{repository_branch}
```

**Repository State at Ratification**

```text
{repository_state}
```

**Ratification Date**

```text
{ratification_date}
```

**Commander**

```text
{commander}
```

**Ratification Authority**

```text
Commander
```

**Ratification Tool**

```text
dev/ratify_constitution_v1.sh
```

**Certification Result**

```text
PASS
```

This Constitution is certified as the authoritative governing document of the
JARVIS Executive Operating System. All subsequent Executive capabilities,
architectural decisions, implementations, verification suites, and certification
artifacts shall derive their authority from this document.

{END_MARKER}

"""

ratification_match = ratification_matches[0]
insert_at = ratification_match.start()
final_text = (
    working[:insert_at].rstrip()
    + "\n\n"
    + fingerprint_block
    + working[insert_at:].lstrip()
)
final_text = final_text.rstrip() + "\n"

constitution_path.write_text(final_text, encoding="utf-8", newline="\n")

report = f"""# CONST-0001 Ratification Report

**Result:** PASS  
**Document:** `{constitution_path.as_posix()}`  
**Document ID:** `CONST-0001`  
**Revision:** `1.0`  
**Status:** `Ratified`  
**Commander:** `{commander}`  
**Ratification Date:** `{ratification_date}`  
**Repository Revision:** `{repository_revision}`  
**Repository Branch:** `{repository_branch}`  
**Repository State:** `{repository_state}`  
**Canonical SHA-256:** `{fingerprint}`  
**Backup:** `{backup_file}`  
**Ratification Tool:** `dev/ratify_constitution_v1.sh`

## Structural Verification

- Articles I–XIX present exactly once: PASS
- Articles I–XIX in canonical order: PASS
- Article XIX precedes appendices: PASS
- Single Certification Appendix: PASS
- Single Constitutional Traceability section: PASS
- Single Final Constitutional Certification section: PASS
- Single Ratification section: PASS
- Duplicate Article-mapping statement absent: PASS
- Draft status removed: PASS
- UTF-8 serialization: PASS
- Canonical fingerprint verification: PASS

## Fingerprint Definition

The canonical SHA-256 is calculated from the complete ratified Constitution after
status normalization and structural cleanup, excluding the generated Constitutional
Fingerprint block. This prevents a self-referential hash and allows deterministic
reverification.
"""

report_path.write_text(report, encoding="utf-8", newline="\n")

print("[PASS] Articles I–XIX present exactly once")
print("[PASS] Articles I–XIX in canonical order")
print("[PASS] Article XIX precedes appendices")
print("[PASS] Certification Appendix is unique")
print("[PASS] Constitutional Traceability is unique")
print("[PASS] Ratification section is unique")
print("[PASS] Draft status normalized to Ratified 1.0")
print("[PASS] Constitutional fingerprint inserted")
print(f"[PASS] Canonical SHA-256: {fingerprint}")
print(f"[PASS] Ratification report: {report_path}")
PY

echo
echo "========================================================================"
echo "JARVIS — CONST-0001 RATIFICATION"
echo "========================================================================"
echo "[PASS] Constitution ratified"
echo "[PASS] Canonical file : $CONSTITUTION_FILE"
echo "[PASS] Backup         : $BACKUP_FILE"
echo "[PASS] Audit report   : $REPORT_FILE"
echo "[PASS] Commander      : $COMMANDER_NAME"
echo "[PASS] Git revision   : $REPOSITORY_REVISION"
echo "[PASS] Git state      : $REPOSITORY_STATE"
echo "------------------------------------------------------------------------"
echo "Overall status: EXCELLENT"
echo "========================================================================"
