#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

JS_FILE="core/src/static/mission_control/health_projection.js"
HTML_FILE="core/src/static/mission_control/index.html"
DOC_FILE="docs/genesis/genesis_vii_a0/GENESIS_VII_A0_PACK_3B_2_2.md"

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
echo "JARVIS — GENESIS VII-A0 PACK 3B-2.2"
echo "EXECUTIVE HEALTH AND RUNTIME PROJECTION"
echo "========================================================================"

require_file \
    "$JS_FILE" \
    "Health projection module exists"

require_file \
    "$HTML_FILE" \
    "Mission Control HTML exists"

require_file \
    "$DOC_FILE" \
    "Pack documentation exists"

require_pattern \
    'class ExecutiveHealthRuntimeProjection' \
    "$JS_FILE" \
    "Canonical health projection"

require_pattern \
    'projectHealth' \
    "$JS_FILE" \
    "Health-check projection"

require_pattern \
    'projectAttention' \
    "$JS_FILE" \
    "Attention projection"

require_pattern \
    'projectRuntime' \
    "$JS_FILE" \
    "Runtime projection"

require_pattern \
    'projectStorage' \
    "$JS_FILE" \
    "Storage projection"

require_pattern \
    'projectMetricCards' \
    "$JS_FILE" \
    "Live metric-card projection"

require_pattern \
    'timeoutMilliseconds: 30000' \
    "$JS_FILE" \
    "Extended initial API timeout"

require_pattern \
    'src="/mission-control/static/health_projection.js"' \
    "$HTML_FILE" \
    "Projection script registration"

app_line="$(
    grep -n 'src="/mission-control/static/app.js"' "$HTML_FILE" \
        | head -1 | cut -d: -f1
)"

api_line="$(
    grep -n 'src="/mission-control/static/api.js"' "$HTML_FILE" \
        | head -1 | cut -d: -f1
)"

dashboard_line="$(
    grep -n 'src="/mission-control/static/dashboard.js"' "$HTML_FILE" \
        | head -1 | cut -d: -f1
)"

health_line="$(
    grep -n 'src="/mission-control/static/health_projection.js"' "$HTML_FILE" \
        | head -1 | cut -d: -f1
)"

if [[
    -n "$app_line" &&
    -n "$api_line" &&
    -n "$dashboard_line" &&
    -n "$health_line" &&
    "$app_line" -lt "$api_line" &&
    "$api_line" -lt "$dashboard_line" &&
    "$dashboard_line" -lt "$health_line"
]]; then
    pass "Canonical frontend load order"
else
    fail "Canonical frontend load order"
fi

if command -v node >/dev/null 2>&1; then
    if node --check "$JS_FILE"; then
        pass "JavaScript syntax"
    else
        fail "JavaScript syntax"
    fi
else
    echo "[SKIP] Node unavailable"
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
