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

        // SITREP R8 executive projection
        sitrepSnapshot: null,
        sitrepLoading: false,
        sitrepTimer: null,
        sitrepScrollTimer: null,
        sitrepScrollIndex: 0,
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

    function knowledgeConversationThread() {
        const answer = byId("knowledge-answer");

        if (!answer) {
            return null;
        }

        if (answer.dataset.chatInitialized !== "true") {
            answer.innerHTML = "";
            answer.dataset.chatInitialized = "true";
            answer.classList.add("knowledge-chat-thread");
            answer.setAttribute("role", "log");
            answer.setAttribute("aria-live", "polite");
            answer.setAttribute("aria-relevant", "additions");
        }

        return answer;
    }

    function scrollKnowledgeConversation() {
        const thread = knowledgeConversationThread();

        if (!thread) {
            return;
        }

        requestAnimationFrame(() => {
            thread.scrollTop = thread.scrollHeight;
        });
    }

    function removePendingKnowledgeMessage() {
        const thread = byId("knowledge-answer");

        if (!thread) {
            return;
        }

        thread
            .querySelectorAll(".knowledge-chat-message--pending")
            .forEach((item) => item.remove());
    }

    function appendKnowledgeMessage(role, text, options = {}) {
        const thread = knowledgeConversationThread();

        if (!thread) {
            return null;
        }

        const message = document.createElement("div");

        const normalizedRole =
            role === "user"
                ? "user"
                : role === "error"
                  ? "error"
                  : "jarvis";

        message.className =
            `knowledge-chat-message knowledge-chat-message--${normalizedRole}`;

        if (options.pending) {
            message.classList.add(
                "knowledge-chat-message--pending",
            );
        }

        const label = document.createElement("div");
        label.className = "knowledge-chat-message-label";
        label.textContent =
            normalizedRole === "user"
                ? "You"
                : normalizedRole === "error"
                  ? "System"
                  : "JARVIS";

        const content = document.createElement("div");
        content.className = "knowledge-chat-message-content";
        content.innerHTML = escapeHtml(value(text))
            .replaceAll("\n", "<br>");

        message.append(label, content);
        thread.appendChild(message);

        scrollKnowledgeConversation();

        return message;
    }

    function renderResponse(response, latencyMs) {
        removePendingKnowledgeMessage();

        appendKnowledgeMessage(
            "jarvis",
            answerFrom(response),
        );

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

        appendKnowledgeMessage(
            "user",
            normalized,
        );

        if (input) {
            input.value = "";
            input.disabled = true;
        }

        appendKnowledgeMessage(
            "jarvis",
            "Searching knowledge…",
            { pending: true },
        );

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

            removePendingKnowledgeMessage();

            appendKnowledgeMessage(
                "error",
                `Knowledge request failed: ${message}`,
            );

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


    /*
     * SITREP R8 — compact Executive security projection.
     * Uses the same authoritative /operations/sitrep endpoint as
     * the full SITREP workspace. It does not invent placeholder events.
     */

    function sitrepSeverity(item) {
        const raw = value(item?.severity).trim().toLowerCase();

        if (["critical", "severe", "extreme"].includes(raw)) {
            return "critical";
        }

        if (["high", "major"].includes(raw)) {
            return "high";
        }

        if (["medium", "moderate", "watch"].includes(raw)) {
            return "medium";
        }

        return "low";
    }

    function sitrepSeverityRank(item) {
        return {
            critical: 4,
            high: 3,
            medium: 2,
            low: 1,
        }[sitrepSeverity(item)] || 0;
    }

    function sitrepWhen(item) {
        const raw = item?.published_at;

        if (!raw) {
            return "TIME N/A";
        }

        const date = new Date(raw);

        if (Number.isNaN(date.getTime())) {
            return "TIME N/A";
        }

        return date.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
        });
    }

    function sitrepAge(item) {
        const raw = item?.published_at;

        if (!raw) {
            return 0;
        }

        const timestamp = new Date(raw).getTime();
        return Number.isFinite(timestamp) ? timestamp : 0;
    }

    function sitrepVisibleEvents(snapshot) {
        const events = Array.isArray(snapshot?.security_events)
            ? snapshot.security_events.slice()
            : [];

        if (!events.length) {
            return [];
        }

        const LIMIT = 20;

        const severityRank = {
            critical: 6,
            extreme: 6,
            severe: 6,
            high: 5,
            major: 5,
            medium: 4,
            moderate: 4,
            watch: 3,
            low: 2,
            info: 1,
        };

        const domainOrder = [
            "military",
            "physical",
            "aviation",
            "maritime",
            "cyber",
            "disaster",
            "reference",
        ];

        function timestamp(event) {
            const value = Date.parse(
                event?.published_at || ""
            );

            return Number.isFinite(value)
                ? value
                : 0;
        }

        function priority(event) {
            const fusion = Number(
                event?.fusion_score
            );

            if (Number.isFinite(fusion)) {
                return fusion;
            }

            const severity = String(
                event?.severity || "low"
            ).toLowerCase();

            return (
                (severityRank[severity] || 0) * 100
            );
        }

        function compare(a, b) {
            const scoreDelta =
                priority(b) - priority(a);

            if (scoreDelta !== 0) {
                return scoreDelta;
            }

            return timestamp(b) - timestamp(a);
        }

        events.sort(compare);

        /*
         * Reserve representation for every active operational
         * domain. This is a display-balancing rule, not an
         * intelligence-confidence judgment.
         *
         * Two records are reserved for each active core domain
         * when possible. Remaining positions are filled globally
         * by fusion priority.
         */
        const CORE_RESERVE = 2;

        const buckets = new Map();

        for (const event of events) {
            const category = String(
                event?.category || "physical"
            ).toLowerCase();

            if (!buckets.has(category)) {
                buckets.set(category, []);
            }

            buckets.get(category).push(event);
        }

        for (const bucket of buckets.values()) {
            bucket.sort(compare);
        }

        const selected = [];
        const selectedIds = new Set();

        function identity(event) {
            return String(
                event?.id ||
                [
                    event?.category || "",
                    event?.published_at || "",
                    event?.title || "",
                ].join("|")
            );
        }

        function add(event) {
            if (!event || selected.length >= LIMIT) {
                return;
            }

            const id = identity(event);

            if (selectedIds.has(id)) {
                return;
            }

            selectedIds.add(id);
            selected.push(event);
        }

        // Known operational domains first.
        for (const category of domainOrder) {
            const bucket = buckets.get(category);

            if (!bucket?.length) {
                continue;
            }

            for (
                let i = 0;
                i < Math.min(
                    CORE_RESERVE,
                    bucket.length
                );
                i += 1
            ) {
                add(bucket[i]);
            }
        }

        /*
         * Future/unknown categories should not disappear simply
         * because the UI predates them. Give each one a single
         * representative if room remains.
         */
        const known = new Set(domainOrder);

        for (const [category, bucket] of buckets) {
            if (
                known.has(category) ||
                !bucket.length ||
                selected.length >= LIMIT
            ) {
                continue;
            }

            add(bucket[0]);
        }

        // Fill all remaining positions from global priority.
        for (const event of events) {
            if (selected.length >= LIMIT) {
                break;
            }

            add(event);
        }

        // Domain reservation controls inclusion only.
        // Actual presentation remains priority ordered.
        selected.sort(compare);

        return selected.slice(0, LIMIT);
    }

    function renderSitrepProjection(snapshot) {
        if (!byId("knowledge-sitrep")) {
            return;
        }

        state.sitrepSnapshot = snapshot;

        const events = sitrepVisibleEvents(snapshot);
        const operationalState =
            value(snapshot?.operational_state, "UNAVAILABLE").toUpperCase();

        const counts = {
            critical: 0,
            high: 0,
            medium: 0,
            low: 0,
        };

        events.forEach((item) => {
            counts[sitrepSeverity(item)] += 1;
        });

        const metric = (id, number) => {
            const element = byId(id);

            if (element) {
                element.textContent = String(number);
            }
        };

        metric("knowledge-sitrep-critical", counts.critical);
        metric("knowledge-sitrep-high", counts.high);
        metric("knowledge-sitrep-medium", counts.medium);
        metric("knowledge-sitrep-low", counts.low);
        metric("knowledge-sitrep-total", events.length);

        /*
         * R8.3 DATASET VISIBILITY
         *
         * The executive feed is intentionally bounded, but this
         * summary describes the complete normalized backend dataset.
         * Counts are descriptive only; fusion_score remains a
         * presentation/triage score, not verification.
         */
        const allEvents = Array.isArray(snapshot?.security_events)
            ? snapshot.security_events
            : [];

        const categoryCounts = allEvents.reduce(
            (counts, item) => {
                const category = String(
                    item?.category || "unknown"
                ).toLowerCase();

                counts[category] =
                    (counts[category] || 0) + 1;

                return counts;
            },
            {},
        );

        const corpus = byId("knowledge-sitrep-corpus");

        if (corpus) {
            const orderedCategories = [
                "military",
                "physical",
                "aviation",
                "maritime",
                "cyber",
                "disaster",
                "reference",
            ];

            const known = new Set(orderedCategories);

            const categoryParts = orderedCategories
                .filter((name) => categoryCounts[name])
                .map(
                    (name) =>
                        `${name.toUpperCase()} ${categoryCounts[name]}`
                );

            Object.keys(categoryCounts)
                .filter((name) => !known.has(name))
                .sort()
                .forEach((name) => {
                    categoryParts.push(
                        `${name.toUpperCase()} ${categoryCounts[name]}`
                    );
                });

            corpus.innerHTML = `
                <strong>${allEvents.length} INGESTED</strong>
                <span>${events.length} PRIORITY DISPLAYED</span>
                ${
                    categoryParts.length
                        ? `<span>${escapeHtml(categoryParts.join(" · "))}</span>`
                        : ""
                }
            `;
        }

        const status = byId("knowledge-sitrep-state");

        if (status) {
            status.textContent = operationalState;
            status.dataset.state = operationalState.toLowerCase();
        }

        const feed = byId("knowledge-sitrep-feed");

        if (feed) {
            if (!events.length) {
                feed.innerHTML = `
                    <div class="knowledge-sitrep-placeholder">
                        ${
                            snapshot?.refreshing
                                ? "Fetching security sources…"
                                : "No current security reports are available. An empty queue does not mean there are no threats."
                        }
                    </div>
                `;
            } else {
                feed.innerHTML = events
                    .map((item, index) => {
                        const severity = sitrepSeverity(item);
                        const source =
                            item?.source?.publisher ||
                            item?.sources?.[0]?.publisher ||
                            "SOURCE";

                        const reports =
                            Number(item?.report_count || 1);

                        return `
                            <article
                                class="knowledge-sitrep-item severity-${severity}"
                                data-sitrep-index="${index}"
                            >
                                <div class="knowledge-sitrep-severity">
                                    ${escapeHtml(severity.toUpperCase())}
                                </div>

                                <time>
                                    ${escapeHtml(sitrepWhen(item))}
                                </time>

                                <div class="knowledge-sitrep-event">
                                    <strong>
                                        ${escapeHtml(item?.title || "Untitled security report")}
                                    </strong>

                                    <span>
                                        ${escapeHtml(
                                            item?.category
                                                ? value(item.category).toUpperCase()
                                                : "SECURITY"
                                        )}
                                        ·
                                        ${escapeHtml(source)}
                                        ${
                                            reports > 1
                                                ? ` · ${reports} REPORTS`
                                                : ""
                                        }
                                    </span>
                                </div>
                            </article>
                        `;
                    })
                    .join("");
            }
        }

        const sources = Array.isArray(snapshot?.sources)
            ? snapshot.sources
            : [];

        const liveSources =
            sources.filter(
                (source) =>
                    value(source?.state).toUpperCase() === "LIVE",
            ).length;

        const health = byId("knowledge-sitrep-source-health");

        if (health) {
            let updated = "UPDATE TIME N/A";

            if (snapshot?.generated_at) {
                const date = new Date(snapshot.generated_at);

                if (!Number.isNaN(date.getTime())) {
                    updated = `UPDATED ${date.toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit",
                    })}`;
                }
            }

            health.textContent =
                `${liveSources}/${sources.length} LIVE SOURCES · ${updated}`;
        }

        startSitrepRoll();
    }

    function startSitrepRoll() {
        clearInterval(state.sitrepScrollTimer);

        const feed = byId("knowledge-sitrep-feed");

        if (!feed) {
            return;
        }

        const items = [...feed.querySelectorAll(".knowledge-sitrep-item")];

        if (items.length < 2) {
            return;
        }

        state.sitrepScrollIndex = 0;

        state.sitrepScrollTimer = window.setInterval(() => {
            if (!feed.isConnected) {
                clearInterval(state.sitrepScrollTimer);
                return;
            }

            state.sitrepScrollIndex =
                (state.sitrepScrollIndex + 1) % items.length;

            items[state.sitrepScrollIndex].scrollIntoView({
                behavior: "smooth",
                block: "nearest",
            });
        }, 4200);
    }

    async function loadSitrepProjection() {
        if (
            state.sitrepLoading ||
            !byId("knowledge-sitrep")
        ) {
            return;
        }

        state.sitrepLoading = true;
        clearTimeout(state.sitrepTimer);

        const controller = new AbortController();
        const timeout = window.setTimeout(
            () => controller.abort(),
            10000,
        );

        try {
            const response = await fetch(
                "/operations/sitrep",
                {
                    headers: {
                        Accept: "application/json",
                    },
                    cache: "no-store",
                    signal: controller.signal,
                },
            );

            if (!response.ok) {
                throw new Error(
                    `SITREP request failed: ${response.status}`,
                );
            }

            renderSitrepProjection(
                await response.json(),
            );
        } catch (error) {
            const retained = state.sitrepSnapshot
                ? JSON.parse(
                    JSON.stringify(state.sitrepSnapshot),
                )
                : {
                    security_events: [],
                    sources: [],
                };

            retained.operational_state =
                state.sitrepSnapshot
                    ? "STALE"
                    : "UNAVAILABLE";

            retained.refreshing = false;

            renderSitrepProjection(retained);
        } finally {
            clearTimeout(timeout);
            state.sitrepLoading = false;

            state.sitrepTimer =
                window.setTimeout(
                    loadSitrepProjection,
                    state.sitrepSnapshot?.refreshing
                        ? 2500
                        : 60000,
                );
        }
    }

    function markup() {
        return `
<section
    class="knowledge-workspace knowledge-workspace--conversation-first"
    aria-labelledby="knowledge-workspace-title"
>
    <section
        class="knowledge-sitrep"
        id="knowledge-sitrep"
        aria-labelledby="knowledge-sitrep-title"
    >
        <header class="knowledge-sitrep-header">
            <div>
                <p class="section-eyebrow">Operational Intelligence</p>
                <h3 id="knowledge-sitrep-title">Live Security Picture</h3>
            </div>

            <span
                id="knowledge-sitrep-state"
                class="knowledge-sitrep-state"
                data-state="connecting"
            >
                CONNECTING
            </span>
        </header>

        <div class="knowledge-sitrep-metrics">
            <span><strong id="knowledge-sitrep-critical">0</strong> CRITICAL</span>
            <span><strong id="knowledge-sitrep-high">0</strong> HIGH</span>
            <span><strong id="knowledge-sitrep-medium">0</strong> MEDIUM</span>
            <span><strong id="knowledge-sitrep-low">0</strong> LOW / INFO</span>
            <span><strong id="knowledge-sitrep-total">0</strong> PRIORITY</span>
        </div>

        <div
            id="knowledge-sitrep-corpus"
            class="knowledge-sitrep-corpus"
            aria-live="polite"
        >
            Waiting for operational dataset…
        </div>

        <div
            id="knowledge-sitrep-feed"
            class="knowledge-sitrep-feed"
            aria-live="polite"
        >
            <div class="knowledge-sitrep-placeholder">
                Connecting to the operational picture…
            </div>
        </div>

        <footer class="knowledge-sitrep-footer">
            <span id="knowledge-sitrep-source-health">
                Connecting to authoritative sources…
            </span>

            <button
                id="knowledge-open-sitrep"
                class="knowledge-sitrep-open"
                type="button"
            >
                Open SITREP →
            </button>
        </footer>
    </section>


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

        byId("knowledge-open-sitrep")?.addEventListener(
            "click",
            () => {
                const trigger = document.querySelector(
                    '[data-command="open-sitrep"], [data-open-view="sitrep"], [data-view="sitrep"]',
                );

                if (trigger instanceof HTMLElement) {
                    trigger.click();
                    return;
                }

                if (
                    window.JARVIS_WORKSPACES &&
                    typeof window.JARVIS_WORKSPACES.open === "function"
                ) {
                    window.JARVIS_WORKSPACES.open("sitrep");
                }
            },
        );

        loadSitrepProjection();

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
