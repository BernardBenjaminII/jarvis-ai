#!/usr/bin/env bash
set -euo pipefail

ROOT="/media/abdullah/JARVISDATA/Projects/jarvis-ai"
UI="$ROOT/core/src/static/mission_control"

INDEX="$UI/index.html"
R32_JS="$UI/executive_shell_r3_2.js"
R32_CSS="$UI/executive_shell_r3_2.css"

R33_JS="$UI/conversation_first_r3_3.js"
R33_CSS="$UI/conversation_first_r3_3.css"

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/.ui_backups/conversation_first_visual_r3_3_${STAMP}"

echo "===================================================================="
echo " JARVIS UI REVISION 3.3"
echo " CONVERSATION-FIRST VISUAL COMPRESSION"
echo "===================================================================="

cd "$ROOT"

for f in \
    "$INDEX" \
    "$R32_JS" \
    "$R32_CSS" \
    "$UI/knowledge_workspace.js" \
    "$UI/knowledge_workspace.css"
do
    [[ -f "$f" ]] || {
        echo "FAIL: required file missing:"
        echo "  $f"
        exit 1
    }
done

# --------------------------------------------------------------------
# Refuse to build R3.3 over an uncertified structural baseline.
# --------------------------------------------------------------------

grep -q 'REVISION = "3.2.2"' "$R32_JS" || {
    echo "FAIL: R3.2.2 structural baseline not detected."
    echo "R3.3 will not install over an unknown DOM revision."
    exit 1
}

mkdir -p "$BACKUP"

cp -a "$INDEX" "$BACKUP/index.html"
cp -a "$R32_JS" "$BACKUP/executive_shell_r3_2.js"
cp -a "$R32_CSS" "$BACKUP/executive_shell_r3_2.css"

[[ ! -f "$R33_JS" ]] || cp -a "$R33_JS" "$BACKUP/conversation_first_r3_3.js"
[[ ! -f "$R33_CSS" ]] || cp -a "$R33_CSS" "$BACKUP/conversation_first_r3_3.css"

echo
echo "Backup:"
echo "  $BACKUP"


# ====================================================================
# R3.3 CSS
#
# IMPORTANT:
#   This file changes PRESENTATION ONLY.
#
#   R3.2.2 remains responsible for:
#       - Knowledge activation
#       - native Knowledge container resolution
#       - DOM consolidation
#       - conversation shell construction
#       - Executive Operations relocation
# ====================================================================

cat > "$R33_CSS" <<'CSS'
/* ==================================================================
   JARVIS UI Revision 3.3
   Conversation-First Visual Compression

   Structural baseline: Revision 3.2.2

   This stylesheet deliberately does NOT alter the Knowledge API,
   form behavior, answer rendering, retrieval, grounding, or backend.
   ================================================================== */


/* ------------------------------------------------------------------
   1. PRIMARY SHELL
   ------------------------------------------------------------------ */

#jarvis-r32-shell[data-revision="3.2.2"] {
    width: 100%;
    max-width: 1180px;
    margin: 0 auto;
    padding: 0 18px 40px;
    box-sizing: border-box;
}


/* ------------------------------------------------------------------
   2. EXECUTIVE STATUS — ONE QUIET TOP LINE
   ------------------------------------------------------------------ */

#jarvis-r32-shell[data-revision="3.2.2"]
#jarvis-r32-status {
    display: flex;
    align-items: center;
    gap: 10px;

    min-height: 38px;
    margin: 0 0 14px;
    padding: 6px 2px;

    border: 0;
    border-bottom: 1px solid var(
        --border-color,
        rgba(127,127,127,.24)
    );

    background: transparent;
    box-shadow: none;
}

#jarvis-r32-shell[data-revision="3.2.2"]
.r322-status-label {
    font-size: 0.76rem;
    font-weight: 600;
    letter-spacing: 0.055em;
    text-transform: uppercase;
    opacity: 0.66;
}

#jarvis-r32-shell[data-revision="3.2.2"]
.r322-status-value {
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.045em;
}

#jarvis-r32-shell[data-revision="3.2.2"]
.r322-status-details {
    margin-left: auto;

    border: 0;
    padding: 5px 8px;

    background: transparent;
    color: inherit;

    font: inherit;
    font-size: 0.76rem;

    opacity: 0.62;
    cursor: pointer;
}

#jarvis-r32-shell[data-revision="3.2.2"]
.r322-status-details:hover,
#jarvis-r32-shell[data-revision="3.2.2"]
.r322-status-details:focus-visible {
    opacity: 1;
}


/* ------------------------------------------------------------------
   3. CONVERSATION IS THE PAGE
   ------------------------------------------------------------------ */

#jarvis-r32-shell[data-revision="3.2.2"]
#jarvis-r32-conversation {
    width: 100%;
    margin: 0;
    padding: 0;

    border: 0;
    background: transparent;
    box-shadow: none;
}


/* ------------------------------------------------------------------
   4. NATIVE KNOWLEDGE CONTAINER

   Keep the real native tree but strip the "application inside an
   application" visual treatment.
   ------------------------------------------------------------------ */

#jarvis-r32-shell[data-revision="3.2.2"]
.r322-native-knowledge {
    width: 100%;
    max-width: none;

    margin: 0;
    padding: 0;

    border: 0;
    background: transparent;
    box-shadow: none;
}


/* ------------------------------------------------------------------
   5. REDUNDANT PROGRESSIVE WORKSPACE CHROME

   These elements remain in the DOM. We only remove their redundant
   visual chrome from the conversation-first presentation.
   ------------------------------------------------------------------ */

#jarvis-r32-shell[data-revision="3.2.2"]
#progressive-workspace-heading {
    display: none !important;
}

#jarvis-r32-shell[data-revision="3.2.2"]
#progressive-workspace-content {
    margin-top: 0 !important;
    padding-top: 0 !important;
}


/* ------------------------------------------------------------------
   6. KNOWLEDGE WORKSPACE — FLATTEN OUTER CARD
   ------------------------------------------------------------------ */

#jarvis-r32-shell[data-revision="3.2.2"]
.knowledge-workspace {
    width: 100%;
    max-width: none;

    margin: 0;
    padding: 0;

    border: 0;
    background: transparent;
    box-shadow: none;
}


/* ------------------------------------------------------------------
   7. QUESTION FORM — PRIMARY COMMAND SURFACE
   ------------------------------------------------------------------ */

#jarvis-r32-shell[data-revision="3.2.2"]
#knowledge-question-form {
    width: 100%;
    margin: 0 0 18px;
}

#jarvis-r32-shell[data-revision="3.2.2"]
#knowledge-question-form textarea,
#jarvis-r32-shell[data-revision="3.2.2"]
#knowledge-question-form input[type="text"],
#jarvis-r32-shell[data-revision="3.2.2"]
#knowledge-question-form input:not([type]) {
    width: 100%;
    box-sizing: border-box;

    min-height: 54px;

    padding: 14px 16px;

    font: inherit;
    font-size: 1rem;
    line-height: 1.45;

    border-radius: 10px;
}

#jarvis-r32-shell[data-revision="3.2.2"]
#knowledge-question-form textarea {
    resize: vertical;
}

#jarvis-r32-shell[data-revision="3.2.2"]
#knowledge-question-form button[type="submit"] {
    min-height: 38px;
    padding: 8px 16px;
}


/* ------------------------------------------------------------------
   8. RESPONSE — READING SURFACE
   ------------------------------------------------------------------ */

#jarvis-r32-shell[data-revision="3.2.2"]
#knowledge-answer {
    width: 100%;
    max-width: none;

    margin: 0;
    padding: 18px 0 8px;

    border: 0;
    background: transparent;
    box-shadow: none;

    font-size: 0.98rem;
    line-height: 1.62;
}

#jarvis-r32-shell[data-revision="3.2.2"]
#knowledge-answer p {
    max-width: 82ch;
}

#jarvis-r32-shell[data-revision="3.2.2"]
#knowledge-answer pre {
    max-width: 100%;
    overflow: auto;
}


/* ------------------------------------------------------------------
   9. KNOWLEDGE METRICS / SMALL STATUS ELEMENTS

   Existing semantic elements are retained. This merely reduces their
   visual weight.
   ------------------------------------------------------------------ */

#jarvis-r32-shell[data-revision="3.2.2"]
.knowledge-metrics,
#jarvis-r32-shell[data-revision="3.2.2"]
.knowledge-metric-grid,
#jarvis-r32-shell[data-revision="3.2.2"]
.knowledge-summary-metrics,
#jarvis-r32-shell[data-revision="3.2.2"]
.knowledge-answer-metrics {
    gap: 8px;
    margin-top: 10px;
}

#jarvis-r32-shell[data-revision="3.2.2"]
.knowledge-metric,
#jarvis-r32-shell[data-revision="3.2.2"]
.metric-card {
    min-height: auto;

    padding: 7px 10px;

    border-radius: 7px;
    box-shadow: none;
}


/* ------------------------------------------------------------------
   10. DETAIL PANELS

   Evidence, Sources, Activity and Technical Details should feel like
   supporting material rather than equal-weight dashboard panels.
   ------------------------------------------------------------------ */

#jarvis-r32-shell[data-revision="3.2.2"]
details {
    box-shadow: none;
}

#jarvis-r32-shell[data-revision="3.2.2"]
details > summary {
    cursor: pointer;
}

#jarvis-r32-shell[data-revision="3.2.2"]
#jarvis-r32-conversation details > summary {
    padding-top: 9px;
    padding-bottom: 9px;
}


/* ------------------------------------------------------------------
   11. EXTERNAL GROUNDED TELEMETRY

   R3.2.2 only puts content here when telemetry is genuinely external
   to the native Knowledge tree.
   ------------------------------------------------------------------ */

#jarvis-r32-shell[data-revision="3.2.2"]
#jarvis-r32-grounding {
    margin-top: 10px;
}

#jarvis-r32-shell[data-revision="3.2.2"]
#jarvis-r32-grounding:empty {
    display: none;
}

#jarvis-r32-shell[data-revision="3.2.2"]
.r322-grounding-disclosure {
    margin: 0;
    padding: 0;

    border: 0;
    background: transparent;
}


/* ------------------------------------------------------------------
   12. EXECUTIVE OPERATIONS — BOTTOM-LINE ROW
   ------------------------------------------------------------------ */

#jarvis-r32-shell[data-revision="3.2.2"]
#jarvis-r32-operations {
    margin: 20px 0 0;
    padding: 0;

    border: 0;
    border-top: 1px solid var(
        --border-color,
        rgba(127,127,127,.24)
    );

    background: transparent;
    box-shadow: none;
}

#jarvis-r32-shell[data-revision="3.2.2"]
#jarvis-r32-operations > summary {
    min-height: 42px;

    display: flex;
    align-items: center;

    padding: 8px 2px;

    font-size: 0.82rem;
    font-weight: 650;
    letter-spacing: 0.025em;

    cursor: pointer;
}

#jarvis-r32-shell[data-revision="3.2.2"]
#jarvis-r32-operations-body {
    padding: 8px 0 20px;
}


/* ------------------------------------------------------------------
   13. HISTORICAL EVENT STREAM

   Available, but it no longer turns the page into a telemetry wall.
   ------------------------------------------------------------------ */

#jarvis-r32-shell[data-revision="3.2.2"]
[data-r32-event-stream="true"] {
    max-height: 300px;
    overflow: auto;
}


/* ------------------------------------------------------------------
   14. MOBILE / NARROW WINDOW
   ------------------------------------------------------------------ */

@media (max-width: 760px) {

    #jarvis-r32-shell[data-revision="3.2.2"] {
        padding-left: 10px;
        padding-right: 10px;
    }

    #jarvis-r32-shell[data-revision="3.2.2"]
    #jarvis-r32-status {
        gap: 7px;
    }

    #jarvis-r32-shell[data-revision="3.2.2"]
    #knowledge-answer {
        font-size: 0.95rem;
    }
}
CSS


# ====================================================================
# R3.3 JAVASCRIPT
#
# This is intentionally tiny.
#
# It does NOT:
#   - move Knowledge
#   - activate Knowledge
#   - clone anything
#   - rebuild forms
#   - intercept requests
#
# It only marks the certified R3.2.2 shell as visually enhanced.
# ====================================================================

cat > "$R33_JS" <<'JS'
(() => {
    "use strict";

    const REVISION = "3.3";

    function apply() {

        const shell =
            document.querySelector(
                '#jarvis-r32-shell[data-revision="3.2.2"]'
            );

        if (!shell) {
            return false;
        }

        if (shell.dataset.visualRevision === REVISION) {
            return true;
        }

        shell.dataset.visualRevision = REVISION;

        document.documentElement.classList.add(
            "jarvis-ui-r3-3"
        );

        console.info(
            "[JARVIS UI R3.3] " +
            "Conversation-first visual compression active."
        );

        return true;
    }


    if (apply()) {
        return;
    }


    const observer =
        new MutationObserver(() => {

            if (apply()) {
                observer.disconnect();
            }
        });


    observer.observe(
        document.documentElement,
        {
            childList: true,
            subtree: true
        }
    );


    window.setTimeout(
        () => observer.disconnect(),
        20000
    );
})();
JS


# ====================================================================
# PATCH LIVE ENTRYPOINT
# ====================================================================

python3 - <<'PY'
from pathlib import Path

index = Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai/"
    "core/src/static/mission_control/index.html"
)

text = index.read_text()

css = (
    '<link rel="stylesheet" '
    'href="/mission-control/static/conversation_first_r3_3.css" />'
)

js = (
    '<script '
    'src="/mission-control/static/conversation_first_r3_3.js" '
    'defer></script>'
)


if "conversation_first_r3_3.css" not in text:

    marker = (
        '<link rel="stylesheet" '
        'href="/mission-control/static/executive_shell_r3_2.css" />'
    )

    if marker not in text:
        raise SystemExit(
            "FAIL: R3.2 CSS load marker not found in index.html"
        )

    text = text.replace(
        marker,
        marker + "\n    " + css,
        1
    )


if "conversation_first_r3_3.js" not in text:

    marker = (
        '<script '
        'src="/mission-control/static/executive_shell_r3_2.js" '
        'defer></script>'
    )

    if marker not in text:
        raise SystemExit(
            "FAIL: R3.2 JS load marker not found in index.html"
        )

    text = text.replace(
        marker,
        marker + "\n    " + js,
        1
    )


index.write_text(text)

print("PASS: index.html references R3.3 assets")
PY


# ====================================================================
# SOURCE CERTIFICATION
# ====================================================================

echo
echo "===================================================================="
echo " SOURCE CERTIFICATION"
echo "===================================================================="

grep -q \
    'conversation_first_r3_3.css' \
    "$INDEX"

echo "PASS: R3.3 CSS load chain"


grep -q \
    'conversation_first_r3_3.js' \
    "$INDEX"

echo "PASS: R3.3 JS load chain"


grep -q \
    'REVISION = "3.3"' \
    "$R33_JS"

echo "PASS: R3.3 revision marker"


grep -q \
    'data-revision="3.2.2"' \
    "$R33_JS"

echo "PASS: R3.3 requires certified R3.2.2 shell"


if grep -Eq \
    'cloneNode|appendChild|insertBefore|navigation\.click|fetch\(' \
    "$R33_JS"
then
    echo "FAIL: R3.3 JS contains structural/network behavior"
    exit 1
else
    echo "PASS: R3.3 JS is presentation-only"
fi


if command -v node >/dev/null 2>&1
then
    node --check "$R33_JS"
    echo "PASS: R3.3 JavaScript syntax"
fi


echo
echo "===================================================================="
echo " REVISION 3.3 INSTALLED"
echo "===================================================================="

echo
echo "Changed:"
echo "  index.html"
echo "  conversation_first_r3_3.css"
echo "  conversation_first_r3_3.js"

echo
echo "Structural baseline preserved:"
echo "  executive_shell_r3_2.js = Revision 3.2.2"

echo
echo "Untouched:"
echo "  knowledge_workspace.js"
echo "  knowledge_workspace.css"
echo "  conversation API"
echo "  catalog grounding"
echo "  retrieval"
echo "  Ollama"
echo "  backend contracts"

echo
echo "Backup:"
echo "  $BACKUP"

echo
echo "Next:"
echo "  ./verify_revision_3_3.sh"

echo "===================================================================="
