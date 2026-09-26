#!/usr/bin/env bash
set -euo pipefail

ROOT="/media/abdullah/JARVISDATA/Projects/jarvis-ai"
UI="$ROOT/core/src/static/mission_control"

INDEX="$UI/index.html"
JS="$UI/executive_shell_r3_2.js"

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/.ui_backups/conversation_first_r3_2_1_${STAMP}"

echo "===================================================================="
echo " JARVIS UI REVISION 3.2.1 — KNOWLEDGE ACTIVATION REPAIR"
echo "===================================================================="

cd "$ROOT"

for f in \
    "$INDEX" \
    "$JS" \
    "$UI/executive_shell_r3_2.css" \
    "$UI/knowledge_workspace.js"
do
    [[ -f "$f" ]] || {
        echo "FAIL: required file missing:"
        echo "  $f"
        exit 1
    }
done

mkdir -p "$BACKUP"

cp -a "$INDEX" "$BACKUP/index.html"
cp -a "$JS" "$BACKUP/executive_shell_r3_2.js"

echo "Backup:"
echo "  $BACKUP"

# --------------------------------------------------------------------
# Replace ONLY the R3.2 JavaScript.
#
# R3.2 failure:
#   It waited for #knowledge-question-form before Knowledge had been
#   activated.
#
# R3.2.1:
#   1. lets Mission Control initialize
#   2. finds native a.navigation-item[data-view="knowledge"]
#   3. activates Knowledge using Mission Control's own navigation event
#   4. waits for Knowledge Workspace to mount
#   5. performs the existing conversation-first relocation
# --------------------------------------------------------------------

cat > "$JS" <<'JS'
(() => {
    "use strict";

    const REVISION = "3.2.1";

    const q = (selector) =>
        document.querySelector(selector);

    const text = (element) =>
        (element?.textContent || "")
            .replace(/\s+/g, " ")
            .trim();


    // ================================================================
    // BASIC DOM HELPERS
    // ================================================================

    function containerFor(element) {

        if (!element) {
            return null;
        }

        return (
            element.closest(
                [
                    "section",
                    "article",
                    ".dashboard-section",
                    ".executive-section",
                    ".panel",
                    ".workspace-panel",
                    ".view-section"
                ].join(",")
            )
            ||
            element.parentElement
        );
    }


    function unique(nodes) {
        return [...new Set(nodes.filter(Boolean))];
    }


    // ================================================================
    // KNOWLEDGE ACTIVATION
    // ================================================================

    function knowledgeNavigation() {

        return q(
            'a.navigation-item[data-view="knowledge"][href="#knowledge"]'
        );
    }


    function knowledgeMounted() {

        return Boolean(
            q("#knowledge-question-form") &&
            q("#knowledge-answer")
        );
    }


    function activateKnowledge() {

        if (knowledgeMounted()) {
            return true;
        }

        const navigation =
            knowledgeNavigation();

        if (!navigation) {

            console.warn(
                "[JARVIS UI R3.2.1] " +
                "Native Knowledge navigation control not found."
            );

            return false;
        }


        /*
         * Use Mission Control's existing navigation contract.
         *
         * We deliberately do NOT directly call Knowledge rendering
         * functions or modify hashes ourselves.
         *
         * The existing application owns view activation.
         */

        navigation.click();

        console.info(
            "[JARVIS UI R3.2.1] " +
            "Native Knowledge view activation requested."
        );

        return true;
    }


    // ================================================================
    // KNOWLEDGE WORKSPACE DISCOVERY
    // ================================================================

    function knowledgeWorkspace() {

        /*
         * Prefer the actual mounted Knowledge component.
         */

        const form =
            q("#knowledge-question-form");

        if (form) {

            const mounted =
                form.closest(
                    [
                        ".knowledge-workspace",
                        "section",
                        "article",
                        ".workspace-panel",
                        ".view-section"
                    ].join(",")
                );

            if (mounted) {
                return mounted;
            }
        }


        /*
         * Fallback to progressive workspace content only after
         * Knowledge has mounted.
         */

        const content =
            q("#progressive-workspace-content");

        if (!content) {
            return null;
        }

        return (
            content.querySelector(".knowledge-workspace")
            ||
            content.closest(
                [
                    "section",
                    "article",
                    ".workspace-panel",
                    ".view-section"
                ].join(",")
            )
            ||
            content
        );
    }


    // ================================================================
    // GROUNDED TELEMETRY
    // ================================================================

    function groundedTelemetry() {

        const heading =
            [...document.querySelectorAll(
                "h1,h2,h3,h4,h5,h6"
            )]
            .find(
                element =>
                    text(element) ===
                    "Grounded Answer Telemetry"
            );

        return containerFor(heading);
    }


    // ================================================================
    // EXECUTIVE STATUS
    // ================================================================

    function executiveState() {

        const raw =
            text(q("#executive-status-heading"));

        if (
            /degrad|deficien|attention|warning/i
                .test(raw)
        ) {
            return "DEGRADED";
        }

        if (
            /healthy|ready|operational/i
                .test(raw)
        ) {
            return "READY";
        }

        return "STATUS";
    }


    // ================================================================
    // EXECUTIVE OPERATIONAL CONTENT
    // ================================================================

    function operationalNodes() {

        const selectors = [

            "#commander-brief-heading",

            "#enterprise-summary-heading",

            "#operational-picture-heading",

            "#executive-attention-heading",

            "#runtime-panel-heading",

            "#storage-panel-heading",

            "#executive-activity-heading",

            "#executive-event-preview-heading",

            "#executive-readiness-heading",

            "#workstreams-heading"
        ];

        return unique(
            selectors.map(
                selector =>
                    containerFor(q(selector))
            )
        );
    }


    // ================================================================
    // R3.2 SHELL INSTALLATION
    // ================================================================

    function installShell() {

        if (q("#jarvis-r32-shell")) {
            return true;
        }


        /*
         * This is the critical R3.2.1 gate.
         *
         * Unlike R3.2, this function is only expected to succeed
         * AFTER native Knowledge activation.
         */

        if (!knowledgeMounted()) {
            return false;
        }


        const knowledge =
            knowledgeWorkspace();

        if (!knowledge) {

            console.warn(
                "[JARVIS UI R3.2.1] " +
                "Knowledge mounted but workspace container " +
                "could not be resolved."
            );

            return false;
        }


        const telemetry =
            groundedTelemetry();

        const operations =
            operationalNodes();


        // ------------------------------------------------------------
        // Construct shell
        // ------------------------------------------------------------

        const shell =
            document.createElement("main");

        shell.id =
            "jarvis-r32-shell";

        shell.dataset.revision =
            REVISION;


        // ------------------------------------------------------------
        // Bottom-line Executive status
        // ------------------------------------------------------------

        const status =
            document.createElement("div");

        status.id =
            "jarvis-r32-status";

        status.innerHTML = `
            <span>
                Executive Status
            </span>

            <strong>
                ${executiveState()}
            </strong>

            <button
                type="button"
                aria-expanded="false"
            >
                Details
            </button>
        `;


        // ------------------------------------------------------------
        // Primary conversation area
        // ------------------------------------------------------------

        const conversation =
            document.createElement("div");

        conversation.id =
            "jarvis-r32-conversation";


        // ------------------------------------------------------------
        // Grounding disclosure
        // ------------------------------------------------------------

        const grounding =
            document.createElement("div");

        grounding.id =
            "jarvis-r32-grounding";


        // ------------------------------------------------------------
        // Executive Operations disclosure
        // ------------------------------------------------------------

        const executive =
            document.createElement("details");

        executive.id =
            "jarvis-r32-operations";

        executive.innerHTML = `
            <summary>
                Executive Operations
            </summary>

            <div
                id="jarvis-r32-operations-body"
            ></div>
        `;


        const operationsBody =
            executive.querySelector(
                "#jarvis-r32-operations-body"
            );


        // ------------------------------------------------------------
        // Determine insertion point
        // ------------------------------------------------------------

        const anchor =
            telemetry
            ||
            operations[0]
            ||
            knowledge;


        if (!anchor?.parentNode) {

            console.error(
                "[JARVIS UI R3.2.1] " +
                "Unable to resolve shell insertion point."
            );

            return false;
        }


        anchor.parentNode.insertBefore(
            shell,
            anchor
        );


        shell.append(
            status,
            conversation,
            grounding,
            executive
        );


        // ============================================================
        // PROMOTE EXISTING KNOWLEDGE WORKSPACE
        // ============================================================

        knowledge.classList.add(
            "r32-moved"
        );

        conversation.appendChild(
            knowledge
        );


        // ============================================================
        // GROUNDED ANSWER TELEMETRY
        // ============================================================

        if (
            telemetry &&
            telemetry !== knowledge &&
            !knowledge.contains(telemetry)
        ) {

            const details =
                document.createElement("details");

            const summary =
                document.createElement("summary");

            summary.textContent =
                "Grounded Answer Telemetry";

            telemetry.classList.add(
                "r32-moved"
            );

            details.append(
                summary,
                telemetry
            );

            grounding.appendChild(
                details
            );
        }


        // ============================================================
        // EXECUTIVE OPERATIONS
        // ============================================================

        operations
            .filter(
                node =>
                    node &&
                    node !== knowledge &&
                    node !== telemetry &&
                    !knowledge.contains(node)
            )
            .forEach(node => {

                node.classList.add(
                    "r32-moved"
                );


                if (
                    node.querySelector?.(
                        "#executive-event-preview-heading"
                    )
                    ||
                    /Recent Executive Events/i
                        .test(text(node))
                ) {

                    node.dataset.r32EventStream =
                        "true";
                }


                operationsBody.appendChild(
                    node
                );
            });


        // ============================================================
        // EXECUTIVE DETAILS BUTTON
        // ============================================================

        const detailsButton =
            status.querySelector("button");


        detailsButton.addEventListener(
            "click",
            () => {

                executive.open = true;

                detailsButton.setAttribute(
                    "aria-expanded",
                    "true"
                );

                executive.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });
            }
        );


        executive.addEventListener(
            "toggle",
            () => {

                detailsButton.setAttribute(
                    "aria-expanded",
                    String(executive.open)
                );
            }
        );


        console.info(
            `[JARVIS UI R${REVISION}] ` +
            "Conversation-first shell installed."
        );

        return true;
    }


    // ================================================================
    // BOOT COORDINATOR
    // ================================================================

    function boot() {

        /*
         * If the shell already exists, nothing to do.
         */

        if (q("#jarvis-r32-shell")) {
            return;
        }


        /*
         * Ask Mission Control to activate Knowledge using its own
         * navigation system.
         */

        activateKnowledge();


        /*
         * Knowledge rendering is asynchronous.
         *
         * Watch for the real form/answer pair to appear.
         */

        let mutationCount = 0;


        const observer =
            new MutationObserver(() => {

                mutationCount += 1;


                if (knowledgeMounted()) {

                    if (installShell()) {

                        observer.disconnect();

                        return;
                    }
                }


                if (mutationCount > 250) {

                    console.warn(
                        "[JARVIS UI R3.2.1] " +
                        "Knowledge activation timed out."
                    );

                    observer.disconnect();
                }
            });


        observer.observe(
            document.body,
            {
                childList: true,
                subtree: true
            }
        );


        /*
         * Also poll briefly.
         *
         * This handles applications that replace innerHTML in ways
         * that may produce an inconvenient mutation sequence.
         */

        let pollCount = 0;


        const poll =
            window.setInterval(
                () => {

                    pollCount += 1;


                    if (
                        knowledgeMounted() &&
                        installShell()
                    ) {

                        window.clearInterval(
                            poll
                        );

                        observer.disconnect();

                        return;
                    }


                    if (pollCount >= 40) {

                        window.clearInterval(
                            poll
                        );

                        observer.disconnect();

                        console.warn(
                            "[JARVIS UI R3.2.1] " +
                            "Knowledge Workspace did not mount " +
                            "within the startup window."
                        );
                    }

                },
                250
            );
    }


    // ================================================================
    // START
    // ================================================================

    if (
        document.readyState ===
        "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            () => {

                /*
                 * Give Mission Control's own DOMContentLoaded handlers
                 * the current event turn before requesting navigation.
                 */

                window.setTimeout(
                    boot,
                    0
                );
            },
            {
                once: true
            }
        );

    } else {

        window.setTimeout(
            boot,
            0
        );
    }

})();
JS


# ====================================================================
# CERTIFY SOURCE
# ====================================================================

echo
echo "===================================================================="
echo " SOURCE CERTIFICATION"
echo "===================================================================="

grep -q \
    'data-view="knowledge"' \
    "$JS"

echo "PASS: native Knowledge navigation contract present"


grep -q \
    'navigation.click()' \
    "$JS"

echo "PASS: native Knowledge activation present"


grep -q \
    'REVISION = "3.2.1"' \
    "$JS"

echo "PASS: revision marker present"


if command -v node >/dev/null 2>&1
then

    node --check "$JS"

    echo "PASS: JavaScript syntax"

fi


echo
echo "===================================================================="
echo " REVISION 3.2.1 INSTALLED"
echo "===================================================================="

echo
echo "Changed:"
echo "  core/src/static/mission_control/executive_shell_r3_2.js"

echo
echo "Unchanged:"
echo "  knowledge_workspace.js"
echo "  knowledge_workspace.css"
echo "  executive_shell_r3_2.css"
echo "  backend"
echo "  retrieval"
echo "  conversation API"
echo "  Ollama/model routing"

echo
echo "Backup:"
echo "  $BACKUP"

echo
echo "Next:"
echo "  ./verify_revision_3_2_1.sh"

echo "===================================================================="
