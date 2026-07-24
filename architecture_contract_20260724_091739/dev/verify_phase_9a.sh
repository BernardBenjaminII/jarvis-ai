#!/usr/bin/env bash

set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCUMENT_PATH="$PROJECT_ROOT/docs/architecture/11_cognitive_architecture.md"

PASS_COUNT=0
FAIL_COUNT=0

print_header() {
    printf '\n'
    printf '%s\n' '======================================================================'
    printf '%s\n' 'JARVIS GEN 2 — PHASE IX-A COGNITIVE ARCHITECTURE'
    printf '%s\n' '======================================================================'
}

pass() {
    PASS_COUNT=$((PASS_COUNT + 1))
    printf '[PASS] %s\n' "$1"
}

fail() {
    FAIL_COUNT=$((FAIL_COUNT + 1))
    printf '[FAIL] %s\n' "$1"
}

require_file() {
    local path="$1"
    local description="$2"

    if [[ -f "$path" ]]; then
        pass "$description"
    else
        fail "$description"
    fi
}

require_text() {
    local pattern="$1"
    local path="$2"
    local description="$3"

    if grep -Fq -- "$pattern" "$path"; then
        pass "$description"
    else
        fail "$description"
    fi
}

require_regex() {
    local pattern="$1"
    local path="$2"
    local description="$3"

    if grep -Eq -- "$pattern" "$path"; then
        pass "$description"
    else
        fail "$description"
    fi
}

print_header

require_file \
    "$DOCUMENT_PATH" \
    "Canonical cognitive architecture document exists"

if [[ ! -f "$DOCUMENT_PATH" ]]; then
    printf '%s\n' '----------------------------------------------------------------------'
    printf 'Checks passed : %d\n' "$PASS_COUNT"
    printf 'Checks failed : %d\n' "$FAIL_COUNT"
    printf '%s\n' 'Overall status: FAILED'
    printf '%s\n' '======================================================================'
    exit 1
fi

require_text \
    '# JARVIS Cognitive Architecture' \
    "$DOCUMENT_PATH" \
    "Canonical document title"

require_text \
    '**Phase:** IX-A' \
    "$DOCUMENT_PATH" \
    "Phase identity"

require_text \
    '# 7. The Cognitive Cycle' \
    "$DOCUMENT_PATH" \
    "Cognitive cycle definition"

require_text \
    '# 21. Cognitive State' \
    "$DOCUMENT_PATH" \
    "Explicit Cognitive State"

require_text \
    '# 22. Working Memory' \
    "$DOCUMENT_PATH" \
    "Working Memory architecture"

require_text \
    '# 31. Attention' \
    "$DOCUMENT_PATH" \
    "Attention governance"

require_text \
    '# 33. Focus Stack' \
    "$DOCUMENT_PATH" \
    "Focus Stack architecture"

require_text \
    '# 39. Interruptions' \
    "$DOCUMENT_PATH" \
    "Interruption architecture"

require_text \
    '# 42. Resume Semantics' \
    "$DOCUMENT_PATH" \
    "Resume semantics"

require_text \
    '# 44. Goal Stack' \
    "$DOCUMENT_PATH" \
    "Goal Stack architecture"

require_text \
    '# 47. Hypotheses' \
    "$DOCUMENT_PATH" \
    "Hypothesis architecture"

require_text \
    '# 50. Confidence Propagation' \
    "$DOCUMENT_PATH" \
    "Confidence propagation"

require_text \
    '# 51. Self-Verification' \
    "$DOCUMENT_PATH" \
    "Self-verification doctrine"

require_text \
    '# 55. Executive Director' \
    "$DOCUMENT_PATH" \
    "Executive Director cognitive responsibility"

require_text \
    '# 60. Model Independence' \
    "$DOCUMENT_PATH" \
    "Model-independent cognition"

require_text \
    '# 63. Cognitive Safety' \
    "$DOCUMENT_PATH" \
    "Cognitive safety architecture"

require_text \
    '# 69. Cognitive Events' \
    "$DOCUMENT_PATH" \
    "Cognitive event architecture"

require_text \
    '# 70. Cognitive Observability' \
    "$DOCUMENT_PATH" \
    "Cognitive observability"

require_text \
    '# 75. Operational Memory Integration' \
    "$DOCUMENT_PATH" \
    "Operational Memory integration"

require_text \
    '# 77. Procedural Memory' \
    "$DOCUMENT_PATH" \
    "Procedural Memory definition"

require_text \
    '# 80. Long-Running Cognition' \
    "$DOCUMENT_PATH" \
    "Long-running cognition"

require_text \
    '# 81. Cross-Device Cognition' \
    "$DOCUMENT_PATH" \
    "Cross-device cognition"

require_text \
    '# 88. Cognitive Invariants' \
    "$DOCUMENT_PATH" \
    "Cognitive invariants"

require_text \
    '# 89. Prohibited Patterns' \
    "$DOCUMENT_PATH" \
    "Prohibited cognitive patterns"

require_text \
    '# 90. Acceptance Criteria' \
    "$DOCUMENT_PATH" \
    "Phase acceptance criteria"

require_text \
    '# 91. Implementation Sequence' \
    "$DOCUMENT_PATH" \
    "Controlled implementation sequence"

require_text \
    'Phase X will redesign Mission Control UI' \
    "$DOCUMENT_PATH" \
    "UI redesign remains explicitly scheduled"

require_text \
    'No model is the mind of JARVIS.' \
    "$DOCUMENT_PATH" \
    "Model independence doctrine"

require_text \
    'No interface owns authoritative cognitive state.' \
    "$DOCUMENT_PATH" \
    "Presentation-state separation invariant"

require_text \
    'Knowledge is permanent.' \
    "$DOCUMENT_PATH" \
    "Constitutional knowledge doctrine"

require_text \
    'Intelligence is upgradable.' \
    "$DOCUMENT_PATH" \
    "Constitutional intelligence doctrine"

require_text \
    'Experience is cumulative.' \
    "$DOCUMENT_PATH" \
    "Constitutional experience doctrine"

require_text \
    'Judgment is earned.' \
    "$DOCUMENT_PATH" \
    "Constitutional judgment doctrine"

if grep -Eq '^EOF$' "$DOCUMENT_PATH"; then
    fail "No stray EOF markers"
else
    pass "No stray EOF markers"
fi

SECTION_COUNT="$(
    grep -Ec '^# [0-9]+\.' "$DOCUMENT_PATH" || true
)"

if [[ "$SECTION_COUNT" -eq 94 ]]; then
    pass "All 94 numbered architecture sections present"
else
    fail "All 94 numbered architecture sections present — found $SECTION_COUNT"
fi

FIRST_SECTION="$(
    grep -E '^# [0-9]+\.' "$DOCUMENT_PATH" \
        | head -n 1 \
        | sed -E 's/^# ([0-9]+)\..*/\1/' \
        || true
)"

LAST_SECTION="$(
    grep -E '^# [0-9]+\.' "$DOCUMENT_PATH" \
        | tail -n 1 \
        | sed -E 's/^# ([0-9]+)\..*/\1/' \
        || true
)"

if [[ "$FIRST_SECTION" == "1" && "$LAST_SECTION" == "94" ]]; then
    pass "Section range is 1 through 94"
else
    fail "Section range is 1 through 94"
fi

DUPLICATE_SECTIONS="$(
    grep -E '^# [0-9]+\.' "$DOCUMENT_PATH" \
        | sed -E 's/^# ([0-9]+)\..*/\1/' \
        | sort -n \
        | uniq -d
)"

if [[ -z "$DUPLICATE_SECTIONS" ]]; then
    pass "No duplicate numbered sections"
else
    fail "No duplicate numbered sections — duplicates: $DUPLICATE_SECTIONS"
fi

MISSING_SECTIONS="$(
    comm -23 \
        <(seq 1 94) \
        <(
            grep -E '^# [0-9]+\.' "$DOCUMENT_PATH" \
                | sed -E 's/^# ([0-9]+)\..*/\1/' \
                | sort -n \
                | uniq
        )
)"

if [[ -z "$MISSING_SECTIONS" ]]; then
    pass "No missing numbered sections"
else
    fail "No missing numbered sections — missing: $MISSING_SECTIONS"
fi

LINE_COUNT="$(wc -l < "$DOCUMENT_PATH")"

if [[ "$LINE_COUNT" -ge 1000 ]]; then
    pass "Document has substantial architectural depth"
else
    fail "Document has substantial architectural depth — only $LINE_COUNT lines"
fi

printf '%s\n' '----------------------------------------------------------------------'
printf 'Checks passed : %d\n' "$PASS_COUNT"
printf 'Checks failed : %d\n' "$FAIL_COUNT"

if [[ "$FAIL_COUNT" -eq 0 ]]; then
    printf '%s\n' 'Overall status: EXCELLENT'
    printf '%s\n' '======================================================================'
    exit 0
fi

printf '%s\n' 'Overall status: FAILED'
printf '%s\n' '======================================================================'
exit 1
