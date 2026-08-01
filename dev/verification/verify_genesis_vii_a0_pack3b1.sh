#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

API_FILE="core/src/static/mission_control/api.js"
HTML_FILE="core/src/static/mission_control/index.html"
DOC_FILE="docs/genesis/genesis_vii_a0/GENESIS_VII_A0_PACK_3B_1.md"

failures=0

pass() {
    printf '[PASS] %s\n' "$1"
}

fail() {
    printf '[FAIL] %s\n' "$1"
    failures=$((failures + 1))
}

require_file() {
    local path="$1"
    local label="$2"

    if [[ -s "$path" ]]; then
        pass "$label"
    else
        fail "$label"
    fi
}

require_pattern() {
    local pattern="$1"
    local path="$2"
    local label="$3"

    if grep -q -- "$pattern" "$path"; then
        pass "$label"
    else
        fail "$label"
    fi
}

echo "========================================================================"
echo "JARVIS — GENESIS VII-A0 PACK 3B-1"
echo "EXECUTIVE API CLIENT"
echo "========================================================================"

require_file "$API_FILE" "Executive API client exists"
require_file "$HTML_FILE" "Mission Control HTML exists"
require_file "$DOC_FILE" "Pack documentation exists"

require_pattern \
    'class ExecutiveApiClient' \
    "$API_FILE" \
    "Canonical API client"

require_pattern \
    'class ExecutiveApiError' \
    "$API_FILE" \
    "Structured API error model"

require_pattern \
    'class ExecutiveApiTimeoutError' \
    "$API_FILE" \
    "Timeout error model"

require_pattern \
    'class ExecutiveApiContractError' \
    "$API_FILE" \
    "Transport contract validation"

require_pattern \
    'calculateRetryDelay' \
    "$API_FILE" \
    "Bounded retry backoff"

require_pattern \
    'AbortController' \
    "$API_FILE" \
    "Request timeout control"

require_pattern \
    'X-JARVIS-Request-ID' \
    "$API_FILE" \
    "Request trace identifier"

require_pattern \
    'window.JARVIS_API = Object.freeze' \
    "$API_FILE" \
    "Stable Executive API interface"

require_pattern \
    'src="/mission-control/api.js"' \
    "$HTML_FILE" \
    "Executive API script registration"

app_line="$(
    grep -n 'src="/mission-control/app.js"' "$HTML_FILE" \
        | head -1 \
        | cut -d: -f1
)"

api_line="$(
    grep -n 'src="/mission-control/api.js"' "$HTML_FILE" \
        | head -1 \
        | cut -d: -f1
)"

if [[ -n "$app_line" && -n "$api_line" && "$app_line" -lt "$api_line" ]]; then
    pass "Executive runtime loads before API client"
else
    fail "Executive runtime loads before API client"
fi

if command -v node >/dev/null 2>&1; then
    if node --check "$API_FILE"; then
        pass "JavaScript syntax"
    else
        fail "JavaScript syntax"
    fi
else
    echo "[SKIP] Node unavailable; browser syntax validation required"
fi

echo
echo "------------------------------------------------------------------------"
echo "Checks failed : $failures"

if [[ "$failures" -eq 0 ]]; then
    echo "Overall status: EXCELLENT"
    echo "========================================================================"
    exit 0
fi

echo "Overall status: REQUIRES CORRECTION"
echo "========================================================================"
exit 1
