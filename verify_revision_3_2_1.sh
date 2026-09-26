#!/usr/bin/env bash
set -euo pipefail

ROOT="/media/abdullah/JARVISDATA/Projects/jarvis-ai"
UI="$ROOT/core/src/static/mission_control"

BASE="${1:-http://127.0.0.1:8000}"

HTML="$(mktemp)"

trap 'rm -f "$HTML"' EXIT


echo "===================================================================="
echo " JARVIS UI REVISION 3.2.1 — VERIFICATION"
echo "===================================================================="


curl -fsS \
    "$BASE/bridge" \
    > "$HTML"


echo
echo "=== LIVE LOAD CHAIN ==="


grep -q \
    'executive_shell_r3_2.css' \
    "$HTML"

echo "PASS: R3.2 CSS live"


grep -q \
    'executive_shell_r3_2.js' \
    "$HTML"

echo "PASS: R3.2.1 JavaScript file live"


if grep -q \
    'executive_shell_r3_1.js' \
    "$HTML"
then

    echo "FAIL: R3.1 JS remains in live page"

    exit 1

else

    echo "PASS: R3.1 JS absent"

fi


echo
echo "=== JAVASCRIPT CONTRACT ==="


grep -q \
    'REVISION = "3.2.1"' \
    "$UI/executive_shell_r3_2.js"

echo "PASS: R3.2.1 source active"


grep -q \
    'a.navigation-item\[data-view="knowledge"\]\[href="#knowledge"\]' \
    "$UI/executive_shell_r3_2.js"

echo "PASS: native Knowledge selector present"


grep -q \
    'navigation.click()' \
    "$UI/executive_shell_r3_2.js"

echo "PASS: native Knowledge activation present"


if command -v node >/dev/null 2>&1
then

    node --check \
        "$UI/executive_shell_r3_2.js"

    echo "PASS: JavaScript syntax"

fi


echo
echo "=== HTTP ASSETS ==="


for path in \
    /mission-control/static/executive_shell_r3_2.css \
    /mission-control/static/executive_shell_r3_2.js
do

    CODE="$(
        curl -sS \
            -o /dev/null \
            -w '%{http_code}' \
            "$BASE$path"
    )"

    printf '%-65s %s\n' \
        "$path" \
        "$CODE"


    [[ "$CODE" == "200" ]] || {

        echo "FAIL: asset unavailable"

        exit 1
    }

done


echo
echo "===================================================================="
echo " PASS: REVISION 3.2.1 IS LIVE"
echo "===================================================================="

echo
echo "Hard-refresh:"
echo
echo "  $BASE/bridge"

echo
echo "Then run this browser-console probe:"
echo

cat <<'PROBE'
({
    revision:
        document.querySelector(
            "#jarvis-r32-shell"
        )?.dataset.revision || null,

    knowledgeNav:
        !!document.querySelector(
            'a.navigation-item[data-view="knowledge"][href="#knowledge"]'
        ),

    knowledgeMounted:
        !!document.querySelector(
            "#knowledge-question-form"
        ),

    shell:
        !!document.querySelector(
            "#jarvis-r32-shell"
        ),

    status:
        !!document.querySelector(
            "#jarvis-r32-status"
        ),

    conversation:
        !!document.querySelector(
            "#jarvis-r32-conversation"
        ),

    knowledgeInsideConversation:
        !!document.querySelector(
            "#jarvis-r32-conversation #knowledge-question-form"
        ),

    operations:
        !!document.querySelector(
            "#jarvis-r32-operations"
        ),

    operationsOpen:
        document.querySelector(
            "#jarvis-r32-operations"
        )?.open ?? null
})
PROBE

echo
echo "Expected:"
echo
echo '  revision: "3.2.1"'
echo "  knowledgeNav: true"
echo "  knowledgeMounted: true"
echo "  shell: true"
echo "  status: true"
echo "  conversation: true"
echo "  knowledgeInsideConversation: true"
echo "  operations: true"
echo "  operationsOpen: false"

echo
echo "===================================================================="
