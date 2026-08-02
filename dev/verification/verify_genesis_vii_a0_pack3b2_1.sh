#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

JS_FILE="core/src/static/mission_control/dashboard.js"
HTML_FILE="core/src/static/mission_control/index.html"
DOC_FILE="docs/genesis/genesis_vii_a0/GENESIS_VII_A0_PACK_3B_2_1.md"

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
echo "JARVIS — GENESIS VII-A0 PACK 3B-2.1"
echo "EXECUTIVE STATUS BANNER PROJECTION"
echo "========================================================================"

require_file \
    "$JS_FILE" \
    "Dashboard projection exists"

require_file \
    "$HTML_FILE" \
    "Mission Control HTML exists"

require_file \
    "$DOC_FILE" \
    "Pack documentation exists"

require_pattern \
    'class ExecutiveStatusBannerProjection' \
    "$JS_FILE" \
    "Status projection controller"

require_pattern \
    'window.JARVIS_API.dashboard' \
    "$JS_FILE" \
    "Canonical Executive API consumption"

require_pattern \
    'executive-status-banner--' \
    "$JS_FILE" \
    "Status banner state projection"

require_pattern \
    'status.attention_items' \
    "$JS_FILE" \
    "Attention item projection"

require_pattern \
    'status.available_metrics' \
    "$JS_FILE" \
    "Metric summary projection"

require_pattern \
    'application.setHealthState' \
    "$JS_FILE" \
    "Executive health state integration"

require_pattern \
    'application.setConnectionState' \
    "$JS_FILE" \
    "REST connection-state integration"

require_pattern \
    'src="/mission-control/static/dashboard.js"' \
    "$HTML_FILE" \
    "Dashboard projection script registration"

app_line="$(
    grep -n 'src="/mission-control/static/app.js"' "$HTML_FILE" \
        | head -1 \
        | cut -d: -f1
)"

api_line="$(
    grep -n 'src="/mission-control/static/api.js"' "$HTML_FILE" \
        | head -1 \
        | cut -d: -f1
)"

dashboard_line="$(
    grep -n 'src="/mission-control/static/dashboard.js"' "$HTML_FILE" \
        | head -1 \
        | cut -d: -f1
)"

if [[
    -n "$app_line" &&
    -n "$api_line" &&
    -n "$dashboard_line" &&
    "$app_line" -lt "$api_line" &&
    "$api_line" -lt "$dashboard_line"
]]; then
    pass "Runtime, API, and projection load order"
else
    fail "Runtime, API, and projection load order"
fi

if command -v node >/dev/null 2>&1; then
    if node --check "$JS_FILE"; then
        pass "JavaScript syntax"
    else
        fail "JavaScript syntax"
    fi
else
    echo "[SKIP] Node unavailable; browser syntax verification required"
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

