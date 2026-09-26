#!/usr/bin/env bash
set -euo pipefail

ROOT="/media/abdullah/JARVISDATA/Projects/jarvis-ai"
UI="$ROOT/core/src/static/mission_control"

BASE="${1:-http://127.0.0.1:8000}"

HTML="$(mktemp)"

trap 'rm -f "$HTML"' EXIT


echo "===================================================================="
echo " JARVIS UI REVISION 3.2.2 — VERIFICATION"
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

echo "PASS: R3.2 JS live"


if grep -q \
    'executive_shell_r3_1.js' \
    "$HTML"
then

    echo "FAIL: R3.1 JS remains live"
    exit 1
else

    echo "PASS: R3.1 JS absent"
fi


echo
echo "=== R3.2.2 SOURCE ==="


grep -q \
    'REVISION = "3.2.2"' \
    "$UI/executive_shell_r3_2.js"

echo "PASS: R3.2.2 source active"


grep -q \
    'nativeKnowledgeContainer' \
    "$UI/executive_shell_r3_2.js"

echo "PASS: consolidation resolver active"


if grep -q \
    'cloneNode' \
    "$UI/executive_shell_r3_2.js"
then

    echo "FAIL: cloning detected"
    exit 1
else

    echo "PASS: no DOM cloning"
fi


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

    [[ "$CODE" == "200" ]] || exit 1

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

    const progressiveHeadings =
        [...document.querySelectorAll("#progressive-workspace-heading")];

    return {
        revision:
            shell?.dataset.revision || null,

        shell:
            !!shell,

        conversation:
            !!conversation,

        knowledgeFormsTotal:
            forms.length,

        knowledgeFormsInsideConversation:
            conversation
                ? forms.filter(
                    node =>
                        conversation.contains(node)
                  ).length
                : 0,

        knowledgeAnswersTotal:
            answers.length,

        knowledgeAnswersInsideConversation:
            conversation
                ? answers.filter(
                    node =>
                        conversation.contains(node)
                  ).length
                : 0,

        progressiveWorkspaceHeadings:
            progressiveHeadings.length,

        progressiveHeadingInsideConversation:
            conversation
                ? progressiveHeadings.filter(
                    node =>
                        conversation.contains(node)
                  ).length
                : 0,

        operations:
            !!operations,

        operationsOpen:
            operations?.open ?? null,

        duplicateKnowledgeForm:
            forms.length !== 1,

        duplicateKnowledgeAnswer:
            answers.length !== 1
    };
})()
PROBE


echo
echo "Expected:"
echo
echo '  revision: "3.2.2"'
echo "  shell: true"
echo "  conversation: true"
echo "  knowledgeFormsTotal: 1"
echo "  knowledgeFormsInsideConversation: 1"
echo "  knowledgeAnswersTotal: 1"
echo "  knowledgeAnswersInsideConversation: 1"
echo "  progressiveWorkspaceHeadings: 1"
echo "  progressiveHeadingInsideConversation: 1"
echo "  operations: true"
echo "  operationsOpen: false"
echo "  duplicateKnowledgeForm: false"
echo "  duplicateKnowledgeAnswer: false"

echo
echo "===================================================================="
