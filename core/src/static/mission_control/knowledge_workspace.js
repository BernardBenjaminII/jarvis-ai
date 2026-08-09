(() => {
    "use strict";

    const state = { mounted: false, submitting: false, sessionId: null };
    const byId = (id) => document.getElementById(id);
    const value = (item, fallback = "") => item === null || item === undefined ? fallback : String(item);
    const escapeHtml = (item) => value(item)
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
                if (current === null || current === undefined || !Object.prototype.hasOwnProperty.call(current, part)) {
                    found = false;
                    break;
                }
                current = current[part];
            }
            if (found && current !== null && current !== undefined) return current;
        }
        return fallback;
    }

    function asArray(item) {
        if (Array.isArray(item)) return item;
        if (item === null || item === undefined) return [];
        if (typeof item === "object") return Object.values(item);
        return [item];
    }

    function setActivity(stage, detail, status = "active") {
        const list = byId("knowledge-activity-list");
        const live = byId("knowledge-live-status");
        if (live) {
            live.textContent = detail || stage;
            live.dataset.status = status;
        }
        if (!list) return;
        const item = document.createElement("li");
        item.className = `knowledge-activity-item knowledge-activity-item--${status}`;
        item.innerHTML = `<span class="knowledge-activity-marker" aria-hidden="true"></span><div><strong>${escapeHtml(stage)}</strong><p>${escapeHtml(detail)}</p></div>`;
        list.appendChild(item);
        list.scrollTop = list.scrollHeight;
    }

    function renderList(id, items, emptyMessage) {
        const element = byId(id);
        if (!element) return;
        if (!items.length) {
            element.innerHTML = `<li>${escapeHtml(emptyMessage)}</li>`;
            return;
        }
        element.innerHTML = items.map((item, index) => {
            if (typeof item === "string") return `<li class="knowledge-inspector-item"><strong>${escapeHtml(item)}</strong></li>`;
            const label = firstDefined(item, ["title", "name", "source_title", "document_title", "path", "file_path", "uri", "id"], `Item ${index + 1}`);
            const detail = firstDefined(item, ["excerpt", "text", "content", "summary", "chunk_text", "document_id", "chunk_id"], "");
            return `<li class="knowledge-inspector-item"><strong>${escapeHtml(label)}</strong>${detail ? `<p>${escapeHtml(detail)}</p>` : ""}</li>`;
        }).join("");
    }

    function answerFrom(response) {
        const answer = firstDefined(response, ["answer", "response", "message", "content", "result.answer", "result.response", "assistant_message.content", "data.answer"], null);
        if (typeof answer === "string" && answer.trim()) return answer.trim();
        if (answer && typeof answer === "object") return JSON.stringify(answer, null, 2);
        return JSON.stringify(response, null, 2);
    }

    function renderResponse(response, latencyMs) {
        const answer = byId("knowledge-answer");
        if (answer) answer.innerHTML = `<div class="knowledge-answer-content">${escapeHtml(answerFrom(response)).replaceAll("\n", "<br>")}</div>`;

        const confidenceRaw = firstDefined(response, ["confidence", "result.confidence", "metadata.confidence", "metadata.executive_knowledge_state.confidence", "knowledge_state.confidence"], null);
        const confidence = byId("knowledge-confidence");
        if (confidence) {
            const numeric = Number(confidenceRaw);
            confidence.textContent = confidenceRaw === null ? "Not reported" : Number.isFinite(numeric) ? `${Math.round(numeric <= 1 ? numeric * 100 : numeric)}%` : value(confidenceRaw);
        }
        const latency = byId("knowledge-latency");
        if (latency) latency.textContent = `${latencyMs} ms`;
        const resultStatus = byId("knowledge-result-status");
        if (resultStatus) resultStatus.textContent = "Completed";

        state.sessionId = value(firstDefined(response, ["session_id", "session.id", "metadata.session_id"], state.sessionId), state.sessionId);
        renderList("knowledge-evidence-list", asArray(firstDefined(response, ["evidence", "grounding.evidence", "metadata.evidence", "metadata.knowledge_grounding.evidence", "metadata.knowledge_grounding.matches", "result.evidence"], [])), "No structured evidence returned by the current API contract.");
        renderList("knowledge-source-list", asArray(firstDefined(response, ["sources", "citations", "grounding.sources", "metadata.sources", "metadata.knowledge_grounding.sources", "result.sources", "result.citations"], [])), "No structured sources returned by the current API contract.");
    }

    async function postJson(endpoint, payload) {
        const response = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json", Accept: "application/json" },
            body: JSON.stringify(payload),
        });
        const raw = await response.text();
        let body;
        try { body = raw ? JSON.parse(raw) : {}; } catch { body = { response: raw }; }
        if (!response.ok) throw new Error(`${endpoint}: ${firstDefined(body, ["detail", "message", "error"], response.statusText)}`);
        return body;
    }

    async function submitQuestion(question) {
        if (state.submitting) return;
        const normalized = value(question).trim();
        if (!normalized) {
            setActivity("Input Required", "Enter a question before submitting.", "error");
            return;
        }

        state.submitting = true;
        const submit = byId("knowledge-submit");
        const input = byId("knowledge-question");
        if (submit) { submit.disabled = true; submit.textContent = "Working…"; }
        if (input) input.disabled = true;
        const list = byId("knowledge-activity-list");
        if (list) list.innerHTML = "";
        const started = performance.now();

        setActivity("Executive", "Receiving knowledge request.", "completed");
        setActivity("Knowledge Directorate", "Searching the canonical catalog.", "active");

        const payload = { question: normalized, mode: "knowledge" };
        if (state.sessionId) payload.session_id = state.sessionId;

        try {
            let response;
            try {
                response = await postJson("/api/knowledge/conversation", {
                    ...payload,
                    context: { workspace: "knowledge" },
                });
            } catch {
                setActivity("Conversation Adapter", "Using compatibility API.", "warning");
                try {
                    response = await postJson("/api/conversation/query", payload);
                } catch {
                    response = await postJson("/ask", {
                        question: normalized,
                        mode: "knowledge",
                    });
                }
            }

            if (Array.isArray(response.activity)) {
                const activityList = byId("knowledge-activity-list");
                if (activityList) activityList.innerHTML = "";
                for (const item of response.activity) {
                    setActivity(
                        item.stage || "Executive",
                        item.detail || "",
                        item.status || "completed",
                    );
                }
            }

            if (response.status === "failed" && response.error) {
                throw new Error(response.error.message || response.error.code);
            }

            renderResponse(
                response,
                Number.isFinite(Number(response.latency_ms))
                    ? Number(response.latency_ms)
                    : Math.round(performance.now() - started),
            );
            setActivity("Knowledge Workspace", "Response ready for inspection.", "ready");
        } catch (error) {
            const message = error instanceof Error ? error.message : value(error);
            setActivity("Request Failed", message, "error");
            const answer = byId("knowledge-answer");
            if (answer) answer.innerHTML = `<div class="knowledge-error-state"><strong>Knowledge request failed</strong><p>${escapeHtml(message)}</p></div>`;
            const resultStatus = byId("knowledge-result-status");
            if (resultStatus) resultStatus.textContent = "Failed";
        } finally {
            state.submitting = false;
            if (submit) { submit.disabled = false; submit.textContent = "Ask JARVIS"; }
            if (input) { input.disabled = false; input.focus(); }
        }
    }

    function markup() {
        return `<section class="knowledge-workspace" aria-labelledby="knowledge-workspace-title">
            <header class="knowledge-workspace-header"><div><p class="section-eyebrow">Mark I · Interactive Knowledge</p><h3 id="knowledge-workspace-title">Knowledge Workspace</h3><p>Ask JARVIS a question and inspect the Executive response, activity, evidence, and sources.</p></div><span id="knowledge-live-status" class="knowledge-status-badge" data-status="ready">Ready</span></header>
            <div class="knowledge-workspace-grid">
                <section class="knowledge-primary-column">
                    <form id="knowledge-question-form" class="knowledge-question-panel"><label for="knowledge-question">Ask JARVIS</label><textarea id="knowledge-question" rows="4" placeholder="Ask a question about the JARVIS knowledge estate" required></textarea><div class="knowledge-question-actions"><p>Uses the existing Executive Conversation API.</p><button id="knowledge-submit" class="primary-button" type="submit">Ask JARVIS</button></div></form>
                    <section class="knowledge-answer-panel" aria-labelledby="knowledge-answer-heading"><header class="knowledge-panel-header"><div><p class="section-eyebrow">Executive response</p><h4 id="knowledge-answer-heading">Answer</h4></div><span id="knowledge-result-status">Ready</span></header><div id="knowledge-answer" aria-live="polite"><div class="knowledge-empty-state"><strong>No question submitted</strong><p>Submit a request to activate catalog grounding and Executive knowledge awareness.</p></div></div><dl class="knowledge-result-metrics"><div><dt>Confidence</dt><dd id="knowledge-confidence">Not reported</dd></div><div><dt>Latency</dt><dd id="knowledge-latency">—</dd></div></dl></section>
                </section>
                <aside class="knowledge-secondary-column">
                    <section class="knowledge-inspector-panel"><header class="knowledge-panel-header"><div><p class="section-eyebrow">Live workflow</p><h4>Executive Activity</h4></div></header><ol id="knowledge-activity-list" class="knowledge-activity-list"></ol></section>
                    <section class="knowledge-inspector-panel"><header class="knowledge-panel-header"><div><p class="section-eyebrow">Grounding</p><h4>Evidence</h4></div></header><ul id="knowledge-evidence-list" class="knowledge-inspector-list"><li>No evidence selected yet.</li></ul></section>
                    <section class="knowledge-inspector-panel"><header class="knowledge-panel-header"><div><p class="section-eyebrow">Provenance</p><h4>Sources</h4></div></header><ul id="knowledge-source-list" class="knowledge-inspector-list"><li>No sources selected yet.</li></ul></section>
                </aside>
            </div>
        </section>`;
    }

    function mount() {
        const content = byId("progressive-workspace-content");
        if (!content) return false;
        const heading = byId("progressive-workspace-heading");
        const description = byId("progressive-workspace-description");
        if (heading) heading.textContent = "Knowledge";
        if (description) description.textContent = "Interactive Executive knowledge retrieval and grounded conversation.";
        content.classList.remove("workspace-placeholder");
        content.classList.add("knowledge-workspace-mount");
        content.innerHTML = markup();
        byId("knowledge-question-form")?.addEventListener("submit", (event) => {
            event.preventDefault();
            submitQuestion(byId("knowledge-question")?.value);
        });
        state.mounted = true;
        setActivity("Knowledge Workspace", "Ready for an Executive knowledge request.", "ready");
        return true;
    }

    function open() {
        const workspace = byId("progressive-workspace");
        if (workspace) { workspace.hidden = false; workspace.removeAttribute("aria-hidden"); }
        mount();
    }

    function isTrigger(target) {
        if (!(target instanceof Element)) return false;
        return Boolean(target.closest('[data-command="open-knowledge"], [data-open-view="knowledge"], [data-view="knowledge"]'));
    }

    document.addEventListener("click", (event) => {
        if (isTrigger(event.target)) setTimeout(open, 0);
    }, true);
    window.addEventListener("hashchange", () => {
        if (location.hash === "#knowledge") setTimeout(open, 0);
    });
    document.addEventListener("DOMContentLoaded", () => {
        if (location.hash === "#knowledge") open();
    });

    window.JARVIS_KNOWLEDGE_WORKSPACE = Object.freeze({ mount, open, submit: submitQuestion, state });
})();
