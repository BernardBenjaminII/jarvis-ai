#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOC="$ROOT/docs/architecture/12_reasoning_architecture.md"

EXPECTED=132
PASS=0
FAIL=0

pass() {
    printf '[PASS] %s\n' "$1"
    PASS=$((PASS+1))
}

fail() {
    printf '[FAIL] %s\n' "$1"
    FAIL=$((FAIL+1))
}

require_text() {
    local TEXT="$1"
    local DESC="$2"

    if grep -Fq "$TEXT" "$DOC"; then
        pass "$DESC"
    else
        fail "$DESC"
    fi
}

require_section() {
    local NUM="$1"
    local TITLE="$2"

    require_text "# ${NUM}. ${TITLE}" \
        "Section ${NUM}: ${TITLE}"
}

echo
echo "======================================================================"
echo "JARVIS GEN 2 — PHASE IX-B"
echo "Explainable Reasoning Architecture Verification"
echo "======================================================================"

[[ -f "$DOC" ]] \
    && pass "Architecture document exists" \
    || {
        fail "Architecture document exists"
        exit 1
    }

require_text "# JARVIS Explainable Reasoning Architecture" \
    "Canonical title"

require_text "**Phase:** IX-B" \
    "Correct phase"

###########################################################
# Core Architecture
###########################################################

require_section 8  "Reasoning Case"
require_section 15 "Evidence Record"
require_section 24 "Claim"
require_section 30 "Hypothesis"
require_section 36 "Alternative"
require_section 43 "Contradiction"
require_section 49 "Confidence"
require_section 54 "Risk"
require_section 71 "Reasoning Director"
require_section 85 "Decision Record"
require_section 94 "Explanation"
require_section 124 "Reasoning Invariants"
require_section 130 "Acceptance Criteria"

###########################################################
# Architectural Invariants
###########################################################

require_text \
"No model owns a Reasoning Case." \
"Model independence"

require_text \
"Raw private model reasoning is not an architectural record." \
"Chain-of-thought boundary"

require_text \
"Reasoning does not write directly into permanent knowledge." \
"Knowledge ownership"

require_text \
"Mission Control renders backend Reasoning State." \
"Mission Control ownership"

###########################################################
# Constitutional Doctrine
###########################################################

require_text \
"Knowledge is permanent." \
"Knowledge doctrine"

require_text \
"Intelligence is upgradable." \
"Intelligence doctrine"

require_text \
"Experience is cumulative." \
"Experience doctrine"

require_text \
"Judgment is earned." \
"Judgment doctrine"

###########################################################
# Numbering Integrity
###########################################################

COUNT=$(grep -Ec '^# [0-9]+\.' "$DOC")

[[ "$COUNT" -eq "$EXPECTED" ]] \
    && pass "132 numbered sections" \
    || fail "Expected 132 sections (found $COUNT)"

FIRST=$(grep -E '^# [0-9]+\.' "$DOC" \
    | head -1 \
    | sed -E 's/^# ([0-9]+).*/\1/')

LAST=$(grep -E '^# [0-9]+\.' "$DOC" \
    | tail -1 \
    | sed -E 's/^# ([0-9]+).*/\1/')

[[ "$FIRST" == "1" && "$LAST" == "$EXPECTED" ]] \
    && pass "Section range 1-$EXPECTED" \
    || fail "Section numbering"

DUPS=$(
grep -E '^# [0-9]+\.' "$DOC" |
sed -E 's/^# ([0-9]+).*/\1/' |
sort |
uniq -d
)

[[ -z "$DUPS" ]] \
    && pass "No duplicate sections" \
    || fail "Duplicate section numbers"

if grep -q '^EOF$' "$DOC"; then
    fail "No stray EOF markers"
else
    pass "No stray EOF markers"
fi

echo "----------------------------------------------------------------------"
echo "Checks passed : $PASS"
echo "Checks failed : $FAIL"

if [[ "$FAIL" -eq 0 ]]; then
    echo "Overall Status : EXCELLENT"
else
    echo "Overall Status : FAILED"
fi

echo "======================================================================"

exit "$FAIL"
