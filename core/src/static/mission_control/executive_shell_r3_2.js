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
