(() => {
    "use strict";

    /*
     * JARVIS Mission Control
     * Revision 3 — Conversation-First Knowledge Workspace
     *
     * Design contract:
     *
     *   - Conversation is the primary interface.
     *   - Grounding remains visible but subordinate.
     *   - Evidence, sources, activity and technical information are
     *     available on demand.
     *   - Existing Executive Conversation APIs remain authoritative.
     *   - No Commander Brief DOM is moved or rewritten.
     */

    const state = {
        mounted: false,
        submitting: false,
        sessionId: null,
    };

    const byId = (id) => document.getElementById(id);

    const value = (item, fallback = "") =>
        item === null || item === undefined ? fallback : String(item);

    const escapeHtml = (item) =>
        value(item)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");

    function firstDefined(object, paths, fallback = null) {
        for (const path of paths) {
            let current = object;
            let found = true;

            for (const part of path.split(".")) {
                if (
                    current === null ||
                    current === undefined ||
                    !Object.prototype.hasOwnProperty.call(current, part)
                ) {
                    found = false;
                    break;
                }

                current = current[part];
            }

            if (
                found &&
                current !== null &&
                current !== undefined
            ) {
                return current;
            }
        }

        return fallback;
    }

    function asArray(item) {
        if (Array.isArray(item)) {
            return item;
        }

        if (item === null || item === undefined) {
            return [];
        }

        if (typeof item === "object") {
            return Object.values(item);
        }

        return [item];
    }

    function answerFrom(response) {
        const answer = firstDefined(
            response,
            [
                "answer",
                "response",
                "message",
                "content",
                "result.answer",
                "result.response",
                "assistant_message.content",
                "data.answer",
            ],
            null,
        );

        if (typeof answer === "string" && answer.trim()) {
            return answer.trim();
        }

        if (answer && typeof answer === "object") {
            return JSON.stringify(answer, null, 2);
        }

        return JSON.stringify(response, null, 2);
    }

    function setStatus(text, status = "ready") {
        const element = byId("knowledge-live-status");

        if (!element) {
            return;
        }

        element.textContent = text;
        element.dataset.status = status;
    }

    function setActivity(stage, detail, status = "active") {
        const list = byId("knowledge-activity-list");

        setStatus(detail || stage, status);

        if (!list) {
            return;
        }

        const item = document.createElement("li");
        item.className =
            `knowledge-activity-item knowledge-activity-item--${status}`;

        item.innerHTML = `
            <span
                class="knowledge-activity-marker"
                aria-hidden="true"
            ></span>

            <div>
                <strong>${escapeHtml(stage)}</strong>
                ${
                    detail
                        ? `<p>${escapeHtml(detail)}</p>`
                        : ""
                }
            </div>
        `;

        list.appendChild(item);
        list.scrollTop = list.scrollHeight;
    }

    function normalizeInspectorItem(item, index) {
        if (typeof item === "string") {
            return {
                label: item,
                detail: "",
            };
        }

        return {
            label: firstDefined(
                item,
                [
                    "title",
                    "name",
                    "source_title",
                    "document_title",
                    "path",
                    "file_path",
                    "uri",
                    "id",
                ],
                `Item ${index + 1}`,
            ),

            detail: firstDefined(
                item,
                [
                    "excerpt",
                    "text",
                    "content",
                    "summary",
                    "chunk_text",
                    "document_id",
                    "chunk_id",
                ],
                "",
            ),
        };
    }

    function renderList(id, items, emptyMessage) {
        const element = byId(id);

        if (!element) {
            return;
        }

        if (!items.length) {
            element.innerHTML =
                `<li class="knowledge-empty-list">${escapeHtml(emptyMessage)}</li>`;
            return;
        }

        element.innerHTML = items
            .map((item, index) => {
                const normalized =
                    normalizeInspectorItem(item, index);

                return `
                    <li class="knowledge-inspector-item">
                        <strong>
                            ${escapeHtml(normalized.label)}
                        </strong>

                        ${
                            normalized.detail
                                ? `<p>${escapeHtml(normalized.detail)}</p>`
                                : ""
                        }
                    </li>
                `;
            })
            .join("");
    }

    function countFrom(response, paths) {
        const item = firstDefined(response, paths, null);

        if (Array.isArray(item)) {
            return item.length;
        }

        if (item && typeof item === "object") {
            return Object.keys(item).length;
        }

        const numeric = Number(item);

        return Number.isFinite(numeric) ? numeric : 0;
    }

    function groundingCounts(response) {
        const sources = asArray(
            firstDefined(
                response,
                [
                    "sources",
                    "citations",
                    "grounding.sources",
                    "metadata.sources",
                    "metadata.knowledge_grounding.sources",
                    "result.sources",
                    "result.citations",
                ],
                [],
            ),
        );

        const evidence = asArray(
            firstDefined(
                response,
                [
                    "evidence",
                    "grounding.evidence",
                    "metadata.evidence",
                    "metadata.knowledge_grounding.evidence",
                    "metadata.knowledge_grounding.matches",
                    "result.evidence",
                ],
                [],
            ),
        );

        const conflicts = countFrom(
            response,
            [
                "conflicts",
                "grounding.conflicts",
                "metadata.conflicts",
                "metadata.knowledge_grounding.conflicts",
            ],
        );

        const accepted = countFrom(
            response,
            [
                "accepted",
                "accepted_count",
                "grounding.accepted",
                "grounding.accepted_count",
                "metadata.accepted",
                "metadata.accepted_count",
                "metadata.knowledge_grounding.accepted",
                "metadata.knowledge_grounding.accepted_count",
            ],
        );

        return {
            sources,
            evidence,
            conflicts,
            accepted:
                accepted ||
                evidence.length,
        };
    }

    function updateMetric(id, content) {
        const element = byId(id);

        if (element) {
            element.textContent = value(content, "—");
        }
    }

    function renderResponse(response, latencyMs) {
        const answer = byId("knowledge-answer");

        if (answer) {
            answer.innerHTML = `
                <div class="knowledge-answer-content">
                    ${escapeHtml(answerFrom(response))
                        .replaceAll("\n", "<br>")}
                </div>
            `;
        }

        const confidenceRaw = firstDefined(
            response,
            [
                "confidence",
                "result.confidence",
                "metadata.confidence",
                "metadata.executive_knowledge_state.confidence",
                "knowledge_state.confidence",
            ],
            null,
        );

        if (confidenceRaw === null) {
            updateMetric(
                "knowledge-confidence",
                "Not reported",
            );
        } else {
            const numeric = Number(confidenceRaw);

            updateMetric(
                "knowledge-confidence",
                Number.isFinite(numeric)
                    ? `${Math.round(
                          numeric <= 1
                              ? numeric * 100
                              : numeric,
                      )}%`
                    : confidenceRaw,
            );
        }

        updateMetric(
            "knowledge-latency",
            `${latencyMs} ms`,
        );

        const grounding = groundingCounts(response);

        updateMetric(
            "knowledge-source-count",
            grounding.sources.length,
        );

        updateMetric(
            "knowledge-evidence-count",
            grounding.evidence.length,
        );

        updateMetric(
            "knowledge-conflict-count",
            grounding.conflicts,
        );

        updateMetric(
            "knowledge-accepted-count",
            grounding.accepted,
        );

        renderList(
            "knowledge-evidence-list",
            grounding.evidence,
            "No structured evidence returned by the current API contract.",
        );

        renderList(
            "knowledge-source-list",
            grounding.sources,
            "No structured sources returned by the current API contract.",
        );

        const rawDetails = firstDefined(
            response,
            [
                "technical_details",
                "metadata.technical_details",
            ],
            null,
        );

        const technicalDetailsContent =
            byId("knowledge-technical-details-content");

        if (technicalDetailsContent) {
            technicalDetailsContent.textContent =
                rawDetails === null ||
                rawDetails === undefined
                    ? "No additional technical details were returned."
                    : typeof rawDetails === "string"
                        ? rawDetails
                        : JSON.stringify(
                              rawDetails,
                              null,
                              2,
                          );
        }

        updateMetric(
            "knowledge-result-status",
            "Completed",
        );

        state.sessionId = value(
            firstDefined(
                response,
                [
                    "session_id",
                    "session.id",
                    "metadata.session_id",
                ],
                state.sessionId,
            ),
            state.sessionId,
        );
    }

    async function postJson(endpoint, payload) {
        const response = await fetch(endpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Accept: "application/json",
            },
            body: JSON.stringify(payload),
        });

        const raw = await response.text();

        let body;

        try {
            body = raw ? JSON.parse(raw) : {};
        } catch {
            body = {
                response: raw,
            };
        }

        if (!response.ok) {
            throw new Error(
                `${endpoint}: ${firstDefined(
                    body,
                    [
                        "detail",
                        "message",
                        "error",
                    ],
                    response.statusText,
                )}`,
            );
        }

        return body;
    }

    async function requestKnowledge(payload) {
        try {
            return await postJson(
                "/api/knowledge/conversation",
                {
                    ...payload,
                    context: {
                        workspace: "knowledge",
                    },
                },
            );
        } catch (primaryError) {
            setActivity(
                "Conversation Adapter",
                "Using compatibility conversation API.",
                "warning",
            );

            try {
                return await postJson(
                    "/api/conversation/query",
                    payload,
                );
            } catch (compatibilityError) {
                setActivity(
                    "Legacy Adapter",
                    "Using legacy knowledge request path.",
                    "warning",
                );

                return postJson(
                    "/ask",
                    {
                        question: payload.question,
                        mode: "knowledge",
                    },
                );
            }
        }
    }

    async function submitQuestion(question) {
        if (state.submitting) {
            return;
        }

        const normalized =
            value(question).trim();

        if (!normalized) {
            setActivity(
                "Input Required",
                "Enter a question before submitting.",
                "error",
            );
            return;
        }

        state.submitting = true;

        const submit =
            byId("knowledge-submit");

        const input =
            byId("knowledge-question");

        const activityList =
            byId("knowledge-activity-list");

        if (submit) {
            submit.disabled = true;
            submit.textContent = "Working…";
        }

        if (input) {
            input.disabled = true;
        }

        if (activityList) {
            activityList.innerHTML = "";
        }

        updateMetric(
            "knowledge-result-status",
            "Working",
        );

        setStatus(
            "Searching knowledge…",
            "active",
        );

        const started =
            performance.now();

        setActivity(
            "Executive",
            "Receiving knowledge request.",
            "completed",
        );

        setActivity(
            "Knowledge Directorate",
            "Searching the canonical catalog.",
            "active",
        );

        const payload = {
            question: normalized,
            mode: "knowledge",
        };

        if (state.sessionId) {
            payload.session_id =
                state.sessionId;
        }

        try {
            const response =
                await requestKnowledge(payload);

            if (
                Array.isArray(response.activity)
            ) {
                if (activityList) {
                    activityList.innerHTML = "";
                }

                for (
                    const item
                    of response.activity
                ) {
                    setActivity(
                        item.stage ||
                            "Executive",
                        item.detail || "",
                        item.status ||
                            "completed",
                    );
                }
            }

            if (
                response.status === "failed" &&
                response.error
            ) {
                throw new Error(
                    response.error.message ||
                        response.error.code,
                );
            }

            const latencyMs =
                Number.isFinite(
                    Number(
                        response.latency_ms,
                    ),
                )
                    ? Number(
                          response.latency_ms,
                      )
                    : Math.round(
                          performance.now() -
                              started,
                      );

            renderResponse(
                response,
                latencyMs,
            );

            setActivity(
                "Knowledge Workspace",
                "Response ready.",
                "ready",
            );

            setStatus(
                "Ready",
                "ready",
            );
        } catch (error) {
            const message =
                error instanceof Error
                    ? error.message
                    : value(error);

            setActivity(
                "Request Failed",
                message,
                "error",
            );

            const answer =
                byId("knowledge-answer");

            if (answer) {
                answer.innerHTML = `
                    <div class="knowledge-error-state">
                        <strong>
                            Knowledge request failed
                        </strong>
                        <p>
                            ${escapeHtml(message)}
                        </p>
                    </div>
                `;
            }

            updateMetric(
                "knowledge-result-status",
                "Failed",
            );

            setStatus(
                "Request failed",
                "error",
            );
        } finally {
            state.submitting = false;

            if (submit) {
                submit.disabled = false;
                submit.textContent =
                    "Ask JARVIS";
            }

            if (input) {
                input.disabled = false;
                input.focus();
            }
        }
    }

    function markup() {
        return `
<section
    class="knowledge-workspace knowledge-workspace--conversation-first"
    aria-labelledby="knowledge-workspace-title"
>
    <header class="knowledge-workspace-header">
        <div class="knowledge-workspace-identity">
            <p class="section-eyebrow">
                Interactive Knowledge
            </p>

            <h3 id="knowledge-workspace-title">
                JARVIS
            </h3>

            <p>
                Ask the Executive knowledge system.
                Grounding and operational detail remain
                available beneath the response.
            </p>
        </div>

        <span
            id="knowledge-live-status"
            class="knowledge-status-badge"
            data-status="ready"
        >
            Ready
        </span>
    </header>


    <main class="knowledge-conversation">

        <form
            id="knowledge-question-form"
            class="knowledge-composer"
        >
            <label
                class="visually-hidden"
                for="knowledge-question"
            >
                Ask JARVIS
            </label>

            <textarea
                id="knowledge-question"
                rows="3"
                placeholder="Ask JARVIS anything about the knowledge estate…"
                required
            ></textarea>

            <div class="knowledge-composer-footer">
                <span>
                    Executive Conversation · Knowledge Mode
                </span>

                <button
                    id="knowledge-submit"
                    class="primary-button"
                    type="submit"
                >
                    Ask JARVIS
                </button>
            </div>
        </form>


        <article
            class="knowledge-response"
            aria-labelledby="knowledge-answer-heading"
        >
            <header class="knowledge-response-header">
                <div>
                    <p class="section-eyebrow">
                        JARVIS
                    </p>

                    <h4 id="knowledge-answer-heading">
                        Response
                    </h4>
                </div>

                <span id="knowledge-result-status">
                    Ready
                </span>
            </header>


            <div
                id="knowledge-answer"
                class="knowledge-answer"
                aria-live="polite"
            >
                <div class="knowledge-empty-state">
                    <strong>
                        Ready for a question
                    </strong>

                    <p>
                        Ask JARVIS to search,
                        reason over, and explain
                        information from the
                        knowledge estate.
                    </p>
                </div>
            </div>


            <dl class="knowledge-result-metrics">

                <div>
                    <dt>Confidence</dt>
                    <dd id="knowledge-confidence">
                        Not reported
                    </dd>
                </div>

                <div>
                    <dt>Sources</dt>
                    <dd id="knowledge-source-count">
                        0
                    </dd>
                </div>

                <div>
                    <dt>Evidence</dt>
                    <dd id="knowledge-evidence-count">
                        0
                    </dd>
                </div>

                <div>
                    <dt>Accepted</dt>
                    <dd id="knowledge-accepted-count">
                        0
                    </dd>
                </div>

                <div>
                    <dt>Conflicts</dt>
                    <dd id="knowledge-conflict-count">
                        0
                    </dd>
                </div>

                <div>
                    <dt>Latency</dt>
                    <dd id="knowledge-latency">
                        —
                    </dd>
                </div>

            </dl>
        </article>


        <section class="knowledge-inspection">

            <details class="knowledge-detail-panel">
                <summary>
                    <span>
                        Evidence
                    </span>

                    <span class="knowledge-detail-hint">
                        Grounding used by the response
                    </span>
                </summary>

                <div class="knowledge-detail-content">
                    <ul
                        id="knowledge-evidence-list"
                        class="knowledge-inspector-list"
                    >
                        <li class="knowledge-empty-list">
                            No evidence selected yet.
                        </li>
                    </ul>
                </div>
            </details>


            <details class="knowledge-detail-panel">
                <summary>
                    <span>
                        Sources
                    </span>

                    <span class="knowledge-detail-hint">
                        Response provenance
                    </span>
                </summary>

                <div class="knowledge-detail-content">
                    <ul
                        id="knowledge-source-list"
                        class="knowledge-inspector-list"
                    >
                        <li class="knowledge-empty-list">
                            No sources selected yet.
                        </li>
                    </ul>
                </div>
            </details>


            <details class="knowledge-detail-panel">
                <summary>
                    <span>
                        Executive Activity
                    </span>

                    <span class="knowledge-detail-hint">
                        Request workflow
                    </span>
                </summary>

                <div class="knowledge-detail-content">
                    <ol
                        id="knowledge-activity-list"
                        class="knowledge-activity-list"
                    ></ol>
                </div>
            </details>


            <details
                id="knowledge-technical-details"
                class="knowledge-detail-panel"
            >
                <summary>
                    <span>
                        Technical Details
                    </span>

                    <span class="knowledge-detail-hint">
                        Raw diagnostic information
                    </span>
                </summary>

                <div class="knowledge-detail-content">
                    <pre
                        id="knowledge-technical-details-content"
                        class="knowledge-technical-details-content"
                    >No additional technical details were returned.</pre>
                </div>
            </details>

        </section>

    </main>
</section>
        `;
    }

    function mount() {
        const content =
            byId(
                "progressive-workspace-content",
            );

        if (!content) {
            return false;
        }

        const heading =
            byId(
                "progressive-workspace-heading",
            );

        const description =
            byId(
                "progressive-workspace-description",
            );

        if (heading) {
            heading.textContent =
                "Knowledge";
        }

        if (description) {
            description.textContent =
                "Conversation-first grounded knowledge.";
        }

        content.classList.remove(
            "workspace-placeholder",
        );

        content.classList.add(
            "knowledge-workspace-mount",
        );

        content.innerHTML =
            markup();

        byId(
            "knowledge-question-form",
        )?.addEventListener(
            "submit",
            (event) => {
                event.preventDefault();

                submitQuestion(
                    byId(
                        "knowledge-question",
                    )?.value,
                );
            },
        );

        /*
         * Enter submits.
         * Shift+Enter inserts a newline.
         */
        byId(
            "knowledge-question",
        )?.addEventListener(
            "keydown",
            (event) => {
                if (
                    event.key === "Enter" &&
                    !event.shiftKey
                ) {
                    event.preventDefault();

                    byId(
                        "knowledge-question-form",
                    )?.requestSubmit();
                }
            },
        );

        state.mounted = true;

        setActivity(
            "Knowledge Workspace",
            "Ready for an Executive knowledge request.",
            "ready",
        );

        setStatus(
            "Ready",
            "ready",
        );

        return true;
    }

    function open() {
        const workspace =
            byId(
                "progressive-workspace",
            );

        if (workspace) {
            workspace.hidden = false;
            workspace.removeAttribute(
                "aria-hidden",
            );
        }

        mount();

        window.requestAnimationFrame(
            () => {
                byId(
                    "knowledge-question",
                )?.focus();
            },
        );
    }

    function isTrigger(target) {
        if (
            !(target instanceof Element)
        ) {
            return false;
        }

        return Boolean(
            target.closest(
                [
                    '[data-command="open-knowledge"]',
                    '[data-open-view="knowledge"]',
                    '[data-view="knowledge"]',
                ].join(","),
            ),
        );
    }

    document.addEventListener(
        "click",
        (event) => {
            if (
                isTrigger(event.target)
            ) {
                setTimeout(
                    open,
                    0,
                );
            }
        },
    );

    window.addEventListener(
        "hashchange",
        () => {
            if (
                location.hash === "#knowledge"
            ) {
                setTimeout(
                    open,
                    0,
                );
            }
        },
    );

    document.addEventListener(
        "DOMContentLoaded",
        () => {
            if (
                location.hash === "#knowledge"
            ) {
                setTimeout(
                    open,
                    0,
                );
            }
        },
    );
})();
