#!/usr/bin/env bash
set -euo pipefail

ROOT="/media/abdullah/JARVISDATA/Projects/jarvis-ai"
UI="$ROOT/core/src/static/mission_control"

INDEX="$UI/index.html"
JS="$UI/executive_shell_r3_2.js"
CSS="$UI/executive_shell_r3_2.css"

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/.ui_backups/native_knowledge_consolidation_r3_2_2_${STAMP}"

echo "===================================================================="
echo " JARVIS UI REVISION 3.2.2"
echo " NATIVE KNOWLEDGE CONTAINER CONSOLIDATION"
echo "===================================================================="

cd "$ROOT"

for f in \
    "$INDEX" \
    "$JS" \
    "$CSS" \
    "$UI/knowledge_workspace.js" \
    "$UI/knowledge_workspace.css"
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
cp -a "$CSS" "$BACKUP/executive_shell_r3_2.css"

echo
echo "Backup:"
echo "  $BACKUP"

# ====================================================================
# R3.2.2 JAVASCRIPT
# ====================================================================

cat > "$JS" <<'JS'
(() => {
    "use strict";

    const REVISION = "3.2.2";

    const q = (selector, root = document) =>
        root.querySelector(selector);

    const qa = (selector, root = document) =>
        [...root.querySelectorAll(selector)];

    const text = (element) =>
        (element?.textContent || "")
            .replace(/\s+/g, " ")
            .trim();


    // ================================================================
    // GENERAL HELPERS
    // ================================================================

    function unique(nodes) {
        return [...new Set(nodes.filter(Boolean))];
    }


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


    function headingByText(value) {

        return qa(
            "h1,h2,h3,h4,h5,h6"
        ).find(
            element =>
                text(element) === value
        );
    }


    // ================================================================
    // NATIVE KNOWLEDGE ACTIVATION
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
                "[JARVIS UI R3.2.2] " +
                "Native Knowledge navigation control not found."
            );

            return false;
        }

        navigation.click();

        console.info(
            "[JARVIS UI R3.2.2] " +
            "Native Knowledge activation requested."
        );

        return true;
    }


    // ================================================================
    // RESOLVE THE COMPLETE NATIVE KNOWLEDGE CONTAINER
    //
    // R3.2.1 could resolve a descendant containing the form.
    //
    // R3.2.2 deliberately walks outward to the Progressive Workspace
    // boundary so the complete native Knowledge view moves as ONE tree.
    // ================================================================

    function nativeKnowledgeContainer() {

        const form =
            q("#knowledge-question-form");

        if (!form) {
            return null;
        }


        // ------------------------------------------------------------
        // Preferred: explicit Progressive Workspace ID
        // ------------------------------------------------------------

        const explicit =
            form.closest("#progressive-workspace");

        if (explicit) {
            return explicit;
        }


        // ------------------------------------------------------------
        // Known progressive workspace heading boundary
        // ------------------------------------------------------------

        const progressiveHeading =
            q("#progressive-workspace-heading");

        if (progressiveHeading) {

            const progressiveContainer =
                containerFor(progressiveHeading);

            if (
                progressiveContainer &&
                progressiveContainer.contains(form)
            ) {
                return progressiveContainer;
            }
        }


        // ------------------------------------------------------------
        // Known progressive content boundary
        // ------------------------------------------------------------

        const progressiveContent =
            q("#progressive-workspace-content");

        if (
            progressiveContent &&
            progressiveContent.contains(form)
        ) {

            const parent =
                progressiveContent.closest(
                    [
                        "#progressive-workspace",
                        "section",
                        "article",
                        ".workspace-panel",
                        ".view-section"
                    ].join(",")
                );

            return parent || progressiveContent;
        }


        // ------------------------------------------------------------
        // Semantic fallback:
        //
        // Find the highest reasonable ancestor that contains BOTH
        // the progressive workspace heading and the Knowledge form.
        // ------------------------------------------------------------

        if (progressiveHeading) {

            let node =
                form.parentElement;

            let candidate =
                null;

            while (
                node &&
                node !== document.body
            ) {

                if (
                    node.contains(progressiveHeading) &&
                    node.contains(form)
                ) {
                    candidate = node;
                }

                node =
                    node.parentElement;
            }

            if (candidate) {
                return candidate;
            }
        }


        // ------------------------------------------------------------
        // Last-resort Knowledge workspace container
        // ------------------------------------------------------------

        return (
            form.closest(".knowledge-workspace")
            ||
            form.closest(
                "section,article,.workspace-panel,.view-section"
            )
            ||
            form.parentElement
        );
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
    // TELEMETRY
    // ================================================================

    function groundedTelemetry() {

        return containerFor(
            headingByText(
                "Grounded Answer Telemetry"
            )
        );
    }


    // ================================================================
    // EXECUTIVE OPERATIONS
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
    // CLEAN R3.2.1 SHELL IF NECESSARY
    //
    // Normally a hard refresh means this is unnecessary.
    // It makes the revision safer during development/hot reload.
    // ================================================================

    function unwrapPreviousShell() {

        const oldShell =
            q("#jarvis-r32-shell");

        if (!oldShell) {
            return;
        }

        const parent =
            oldShell.parentNode;

        if (!parent) {
            return;
        }


        const oldConversation =
            q(
                "#jarvis-r32-conversation",
                oldShell
            );

        const oldGrounding =
            q(
                "#jarvis-r32-grounding",
                oldShell
            );

        const oldOperations =
            q(
                "#jarvis-r32-operations-body",
                oldShell
            );


        [
            oldConversation,
            oldGrounding,
            oldOperations
        ]
        .filter(Boolean)
        .forEach(host => {

            while (host.firstChild) {

                parent.insertBefore(
                    host.firstChild,
                    oldShell
                );
            }
        });


        oldShell.remove();
    }


    // ================================================================
    // SHELL INSTALLATION
    // ================================================================

    function installShell() {

        const existing =
            q("#jarvis-r32-shell");

        if (
            existing &&
            existing.dataset.revision === REVISION
        ) {
            return true;
        }


        if (!knowledgeMounted()) {
            return false;
        }


        if (existing) {
            unwrapPreviousShell();
        }


        const knowledge =
            nativeKnowledgeContainer();

        if (!knowledge) {

            console.warn(
                "[JARVIS UI R3.2.2] " +
                "Unable to resolve native Knowledge container."
            );

            return false;
        }


        const telemetry =
            groundedTelemetry();


        const operations =
            operationalNodes()
                .filter(
                    node =>
                        node &&
                        node !== knowledge &&
                        !knowledge.contains(node) &&
                        !node.contains(knowledge)
                );


        // ============================================================
        // SHELL
        // ============================================================

        const shell =
            document.createElement("main");

        shell.id =
            "jarvis-r32-shell";

        shell.dataset.revision =
            REVISION;


        // ============================================================
        // STATUS
        // ============================================================

        const status =
            document.createElement("div");

        status.id =
            "jarvis-r32-status";

        status.innerHTML = `
            <span class="r322-status-label">
                Executive Status
            </span>

            <strong class="r322-status-value">
                ${executiveState()}
            </strong>

            <button
                type="button"
                class="r322-status-details"
                aria-expanded="false"
            >
                Details
            </button>
        `;


        // ============================================================
        // PRIMARY KNOWLEDGE / CONVERSATION HOST
        // ============================================================

        const conversation =
            document.createElement("section");

        conversation.id =
            "jarvis-r32-conversation";

        conversation.setAttribute(
            "aria-label",
            "JARVIS Conversation"
        );


        // ============================================================
        // GROUNDING HOST
        // ============================================================

        const grounding =
            document.createElement("div");

        grounding.id =
            "jarvis-r32-grounding";


        // ============================================================
        // EXECUTIVE OPERATIONS
        // ============================================================

        const executive =
            document.createElement("details");

        executive.id =
            "jarvis-r32-operations";

        executive.innerHTML = `
            <summary>
                <span>
                    Executive Operations
                </span>
            </summary>

            <div
                id="jarvis-r32-operations-body"
            ></div>
        `;


        const operationsBody =
            q(
                "#jarvis-r32-operations-body",
                executive
            );


        // ============================================================
        // INSERT BEFORE THE NATIVE KNOWLEDGE CONTAINER
        // ============================================================

        const parent =
            knowledge.parentNode;

        if (!parent) {

            console.error(
                "[JARVIS UI R3.2.2] " +
                "Native Knowledge container has no parent."
            );

            return false;
        }


        parent.insertBefore(
            shell,
            knowledge
        );


        shell.append(
            status,
            conversation,
            grounding,
            executive
        );


        // ============================================================
        // MOVE THE COMPLETE NATIVE KNOWLEDGE TREE ONCE
        // ============================================================

        knowledge.classList.add(
            "r32-moved",
            "r322-native-knowledge"
        );

        conversation.appendChild(
            knowledge
        );


        // ============================================================
        // GROUNDING TELEMETRY
        //
        // Only relocate telemetry if it is genuinely external to the
        // Knowledge container. If Knowledge already owns it, leave it.
        // ============================================================

        if (
            telemetry &&
            telemetry !== knowledge &&
            !knowledge.contains(telemetry) &&
            !telemetry.contains(knowledge)
        ) {

            const details =
                document.createElement("details");

            details.className =
                "r322-grounding-disclosure";


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
        // MOVE EXECUTIVE CONTENT
        // ============================================================

        operations.forEach(node => {

            /*
             * Do not move the shell itself or any ancestor of it.
             */

            if (
                node === shell ||
                node.contains(shell) ||
                shell.contains(node)
            ) {
                return;
            }


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
        // STATUS → EXECUTIVE OPERATIONS
        // ============================================================

        const detailsButton =
            q(
                ".r322-status-details",
                status
            );


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


        // ============================================================
        // CERTIFICATION MARKERS
        // ============================================================

        shell.dataset.knowledgeForms =
            String(
                qa(
                    "#knowledge-question-form",
                    shell
                ).length
            );


        shell.dataset.knowledgeAnswers =
            String(
                qa(
                    "#knowledge-answer",
                    shell
                ).length
            );


        console.info(
            `[JARVIS UI R${REVISION}] ` +
            "Native Knowledge container consolidated."
        );


        return true;
    }


    // ================================================================
    // BOOT
    // ================================================================

    function boot() {

        activateKnowledge();


        let finished =
            false;


        const finish = () => {

            if (finished) {
                return true;
            }


            if (
                knowledgeMounted() &&
                installShell()
            ) {

                finished = true;

                return true;
            }


            return false;
        };


        if (finish()) {
            return;
        }


        const observer =
            new MutationObserver(
                () => {

                    if (finish()) {
                        observer.disconnect();
                    }
                }
            );


        observer.observe(
            document.body,
            {
                childList: true,
                subtree: true
            }
        );


        let attempts =
            0;


        const poll =
            window.setInterval(
                () => {

                    attempts += 1;


                    if (finish()) {

                        window.clearInterval(
                            poll
                        );

                        observer.disconnect();

                        return;
                    }


                    if (attempts >= 60) {

                        window.clearInterval(
                            poll
                        );

                        observer.disconnect();


                        console.warn(
                            "[JARVIS UI R3.2.2] " +
                            "Knowledge consolidation timed out."
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
            () =>
                window.setTimeout(
                    boot,
                    0
                ),
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
# APPEND R3.2.2-SPECIFIC CSS
# ====================================================================

cat >> "$CSS" <<'CSS'


/* ==================================================================
   JARVIS UI Revision 3.2.2
   Native Knowledge Container Consolidation
   ================================================================== */

#jarvis-r32-shell[data-revision="3.2.2"] {
    display: block;
}

#jarvis-r32-shell[data-revision="3.2.2"]
#jarvis-r32-conversation {
    display: block;
    width: 100%;
}

#jarvis-r32-shell[data-revision="3.2.2"]
.r322-native-knowledge {
    width: 100%;
    max-width: none;
    margin: 0;
}

#jarvis-r32-shell[data-revision="3.2.2"]
#jarvis-r32-grounding:empty {
    display: none;
}

#jarvis-r32-shell[data-revision="3.2.2"]
.r322-grounding-disclosure {
    margin-top: 12px;
}

#jarvis-r32-shell[data-revision="3.2.2"]
#jarvis-r32-operations {
    margin-top: 16px;
}

/*
 * Historical executive events remain callable but do not dominate the
 * conversation-first workspace.
 */
#jarvis-r32-shell[data-revision="3.2.2"]
[data-r32-event-stream="true"] {
    max-height: 420px;
    overflow: auto;
}
CSS


# ====================================================================
# SOURCE CERTIFICATION
# ====================================================================

echo
echo "===================================================================="
echo " SOURCE CERTIFICATION"
echo "===================================================================="


grep -q \
    'REVISION = "3.2.2"' \
    "$JS"

echo "PASS: revision marker"


grep -q \
    'nativeKnowledgeContainer' \
    "$JS"

echo "PASS: native Knowledge container resolver"


grep -q \
    'data-view="knowledge"' \
    "$JS"

echo "PASS: native Knowledge navigation contract"


grep -q \
    'conversation.appendChild' \
    "$JS"

echo "PASS: existing DOM relocation path"


if grep -q \
    'cloneNode' \
    "$JS"
then

    echo "FAIL: cloneNode detected"
    exit 1

else

    echo "PASS: no DOM cloning"

fi


if command -v node >/dev/null 2>&1
then

    node --check "$JS"

    echo "PASS: JavaScript syntax"

fi


echo
echo "===================================================================="
echo " REVISION 3.2.2 INSTALLED"
echo "===================================================================="

echo
echo "Changed:"
echo "  executive_shell_r3_2.js"
echo "  executive_shell_r3_2.css"

echo
echo "Preserved:"
echo "  index.html load chain"
echo "  knowledge_workspace.js"
echo "  knowledge_workspace.css"
echo "  conversation API"
echo "  catalog grounding"
echo "  retrieval"
echo "  Ollama/model routing"
echo "  backend contracts"

echo
echo "Backup:"
echo "  $BACKUP"

echo
echo "Next:"
echo "  ./verify_revision_3_2_2.sh"

echo "===================================================================="
