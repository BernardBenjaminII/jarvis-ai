#!/usr/bin/env bash
set -euo pipefail

ROOT="/media/abdullah/JARVISDATA/Projects/jarvis-ai"
UI="$ROOT/core/src/static/mission_control"
BASE="${1:-http://127.0.0.1:8000}"

HTML="$(mktemp)"
trap 'rm -f "$HTML"' EXIT


echo "===================================================================="
echo " JARVIS UI REVISION 3.3 — VERIFICATION"
echo "===================================================================="

curl -fsS "$BASE/bridge" > "$HTML"


echo
echo "=== STRUCTURAL BASELINE ==="

grep -q \
    'REVISION = "3.2.2"' \
    "$UI/executive_shell_r3_2.js"

echo "PASS: R3.2.2 remains structural baseline"


echo
echo "=== LIVE LOAD CHAIN ==="

for asset in \
    executive_shell_r3_2.css \
    conversation_first_r3_3.css \
    executive_shell_r3_2.js \
    conversation_first_r3_3.js
do
    grep -q "$asset" "$HTML" || {
        echo "FAIL: missing from /bridge: $asset"
        exit 1
    }

    echo "PASS: $asset"
done


echo
echo "=== R3.3 SOURCE ==="

grep -q \
    'REVISION = "3.3"' \
    "$UI/conversation_first_r3_3.js"

echo "PASS: visual revision marker"


if grep -Eq \
    'cloneNode|appendChild|insertBefore|navigation\.click|fetch\(' \
    "$UI/conversation_first_r3_3.js"
then
    echo "FAIL: structural/network operation found in R3.3"
    exit 1
else
    echo "PASS: presentation-only JS"
fi


if command -v node >/dev/null 2>&1
then
    node --check "$UI/conversation_first_r3_3.js"
    echo "PASS: JavaScript syntax"
fi


echo
echo "=== HTTP ASSETS ==="

for path in \
    /mission-control/static/executive_shell_r3_2.css \
    /mission-control/static/conversation_first_r3_3.css \
    /mission-control/static/executive_shell_r3_2.js \
    /mission-control/static/conversation_first_r3_3.js
do
    CODE="$(
        curl -sS \
            -o /dev/null \
            -w '%{http_code}' \
            "$BASE$path"
    )"

    printf '%-70s %s\n' "$path" "$CODE"

    [[ "$CODE" == "200" ]] || {
        echo "FAIL: asset unavailable"
        exit 1
    }
done


echo
echo "===================================================================="
echo " STATIC VERIFICATION PASS"
echo "===================================================================="

echo
echo "Hard-refresh:"
echo
echo "  $BASE/bridge"

echo
echo "Then run this browser-console certification:"
echo

cat <<'PROBE'
(() => {
    const shell =
        document.querySelector("#jarvis-r32-shell");

    const conversation =
        document.querySelector("#jarvis-r32-conversation");

    const operations =
        document.querySelector("#jarvis-r32-operations");

    const forms =
        [...document.querySelectorAll("#knowledge-question-form")];

    const answers =
        [...document.querySelectorAll("#knowledge-answer")];

    const progressiveHeading =
        document.querySelector("#progressive-workspace-heading");

    const headingStyle =
        progressiveHeading
            ? getComputedStyle(progressiveHeading)
            : null;

    return {
        structuralRevision:
            shell?.dataset.revision || null,

        visualRevision:
            shell?.dataset.visualRevision || null,

        shell:
            !!shell,

        conversation:
            !!conversation,

        knowledgeFormsTotal:
            forms.length,

        knowledgeFormsInsideConversation:
            conversation
                ? forms.filter(
                    node => conversation.contains(node)
                  ).length
                : 0,

        knowledgeAnswersTotal:
            answers.length,

        knowledgeAnswersInsideConversation:
            conversation
                ? answers.filter(
                    node => conversation.contains(node)
                  ).length
                : 0,

        duplicateKnowledgeForm:
            forms.length !== 1,

        duplicateKnowledgeAnswer:
            answers.length !== 1,

        progressiveHeadingExists:
            !!progressiveHeading,

        progressiveHeadingVisuallyHidden:
            headingStyle
                ? headingStyle.display === "none"
                : null,

        operations:
            !!operations,

        operationsOpen:
            operations?.open ?? null,

        r33Stylesheet:
            [...document.styleSheets]
                .some(
                    sheet =>
                        sheet.href?.includes(
                            "conversation_first_r3_3.css"
                        )
                ),

        r33Script:
            [...document.scripts]
                .some(
                    script =>
                        script.src?.includes(
                            "conversation_first_r3_3.js"
                        )
                )
    };
})()
PROBE


echo
echo "Expected:"
echo
echo '  structuralRevision: "3.2.2"'
echo '  visualRevision: "3.3"'
echo "  shell: true"
echo "  conversation: true"
echo "  knowledgeFormsTotal: 1"
echo "  knowledgeFormsInsideConversation: 1"
echo "  knowledgeAnswersTotal: 1"
echo "  knowledgeAnswersInsideConversation: 1"
echo "  duplicateKnowledgeForm: false"
echo "  duplicateKnowledgeAnswer: false"
echo "  progressiveHeadingExists: true"
echo "  progressiveHeadingVisuallyHidden: true"
echo "  operations: true"
echo "  operationsOpen: false"
echo "  r33Stylesheet: true"
echo "  r33Script: true"

echo
echo "===================================================================="
