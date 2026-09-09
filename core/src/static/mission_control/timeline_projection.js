/* =============================================================================
   GENESIS VII-A0 — PACK 4B-1
   MISSION CONTROL EXECUTIVE EVENT TIMELINE PROJECTION
   ============================================================================= */

"use strict";

(() => {
    const MODULE_NAME = "executiveEventTimelineProjection";
    const MODULE_VERSION = "Genesis VII-A0 Pack 4B-1";

    const CONFIGURATION = Object.freeze({
        restEndpoint: "/operations/executive/events",
        liveEndpoint: "/operations/executive/live",
        initialLimit: 100,
        maximumEvents: 250,
        requestTimeoutMilliseconds: 30000,
        fallbackPollMilliseconds: 15000,
        reconnectBaseMilliseconds: 1000,
        reconnectMaximumMilliseconds: 30000,
    });

    const EventState = Object.freeze({
        CONNECTING: "connecting",
        LIVE: "live",
        POLLING: "polling",
        DEGRADED: "degraded",
        STOPPED: "stopped",
    });

    const SeverityByKind = Object.freeze({
        executive_failure: "critical",
        mission_failed: "critical",
        task_failed: "critical",
        recovery_refused: "critical",

        mission_blocked: "warning",
        task_blocked: "warning",
        health_state_changed: "warning",
        session_suspended: "warning",

        executive_boot_completed: "success",
        mission_completed: "success",
        task_completed: "success",
        activity_completed: "success",
        checkpoint_verified: "success",
        recovery_completed: "success",

        executive_boot_started: "information",
        executive_shutdown_started: "information",
        executive_shutdown_completed: "information",
        mission_started: "information",
        task_started: "information",
        activity_started: "information",
        capability_registered: "information",
        director_registered: "information",
        director_unregistered: "information",
        director_readiness_changed: "information",
    });

    const KindLabels = Object.freeze({
        executive_boot_started: "Executive boot started",
        executive_boot_completed: "Executive boot completed",
        executive_shutdown_started: "Executive shutdown started",
        executive_shutdown_completed: "Executive shutdown completed",
        executive_failure: "Executive failure",
        session_created: "Session created",
        session_activated: "Session activated",
        session_suspended: "Session suspended",
        session_resumed: "Session resumed",
        session_completed: "Session completed",
        session_aborted: "Session aborted",
        mission_created: "Mission created",
        mission_started: "Mission started",
        mission_completed: "Mission completed",
        mission_aborted: "Mission aborted",
        mission_failed: "Mission failed",
        mission_blocked: "Mission blocked",
        objective_started: "Objective started",
        objective_completed: "Objective completed",
        task_started: "Task started",
        task_completed: "Task completed",
        task_failed: "Task failed",
        task_blocked: "Task blocked",
        activity_started: "Activity started",
        activity_completed: "Activity completed",
        observation_received: "Observation received",
        knowledge_retrieved: "Knowledge retrieved",
        reasoning_started: "Reasoning started",
        hypothesis_generated: "Hypothesis generated",
        hypothesis_selected: "Hypothesis selected",
        decision_proposed: "Decision proposed",
        decision_certified: "Decision certified",
        checkpoint_started: "Checkpoint started",
        checkpoint_created: "Checkpoint created",
        checkpoint_verified: "Checkpoint verified",
        recovery_started: "Recovery started",
        recovery_completed: "Recovery completed",
        recovery_refused: "Recovery refused",
        operator_command: "Operator command",
        note_recorded: "Note recorded",
        health_state_changed: "Health state changed",
        capability_registered: "Capability registered",
        director_registered: "Director registered",
        director_unregistered: "Director unregistered",
        director_readiness_changed: "Director readiness changed",
    });

    const normalizeString = (value) => String(value ?? "").trim();

    const escapeForDisplay = (value) => {
        if (value === null || value === undefined) {
            return "";
        }

        if (typeof value === "string") {
            return value;
        }

        try {
            return JSON.stringify(value);
        } catch {
            return String(value);
        }
    };

    const formatTimestamp = (value) => {
        const timestamp = new Date(value);

        if (Number.isNaN(timestamp.getTime())) {
            return {
                machine: "",
                time: "Unknown time",
                full: "Timestamp unavailable",
            };
        }

        return {
            machine: timestamp.toISOString(),
            time: timestamp.toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
            }),
            full: timestamp.toLocaleString([], {
                year: "numeric",
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
            }),
        };
    };

    const humanize = (value) => {
        const normalized = normalizeString(value);

        if (!normalized) {
            return "Executive event";
        }

        return normalized
            .replace(/[_-]+/g, " ")
            .replace(/\b\w/g, (character) => character.toUpperCase());
    };

    class ExecutiveEventTimelineProjection {
        constructor() {
            this.application = null;
            this.elements = {};
            this.eventsById = new Map();
            this.socket = null;
            this.socketGeneration = 0;
            this.reconnectAttempt = 0;
            this.reconnectTimer = null;
            this.pollTimer = null;
            this.refreshPromise = null;
            this.stopped = false;
        }

        async initialize(application) {
            this.application = application;
            this.cacheElements();
            this.setState(EventState.CONNECTING, "Loading certified history");

            application.state.set(
                "runtime.executiveEventTimelineProjection",
                {
                    state: "ready",
                    version: MODULE_VERSION,
                    initializedAt: new Date().toISOString(),
                },
                {
                    source: MODULE_NAME,
                }
            );

            await this.refreshHistory();
            this.connectLiveTransport();
        }

        cacheElements() {
            this.elements.panel =
                document.querySelector("#executive-activity-panel") ??
                document.querySelector(
                    ".dashboard-panel--timeline"
                );

            this.elements.timeline =
                document.querySelector("#executive-event-timeline") ??
                document.querySelector(".event-timeline");

            if (!this.elements.timeline) {
                throw new Error(
                    "Mission Control Executive event timeline was not found."
                );
            }

            this.elements.status =
                document.querySelector("#event-stream-status") ??
                this.createStatusElement();

            this.elements.count =
                document.querySelector("#event-stream-count") ??
                this.createCountElement();

            this.elements.updated =
                document.querySelector("#event-stream-updated") ??
                this.createUpdatedElement();

            this.elements.refreshButton =
                document.querySelector("#event-stream-refresh");

            if (this.elements.refreshButton) {
                this.elements.refreshButton.addEventListener(
                    "click",
                    () => {
                        void this.refreshHistory({
                            force: true,
                        });
                    }
                );
            }

            this.removePackPlaceholder();
        }

        createStatusElement() {
            const status = document.createElement("span");
            status.id = "event-stream-status";
            status.className =
                "event-stream-status event-stream-status--connecting";
            status.textContent = "Connecting";

            const header =
                this.elements.panel?.querySelector(
                    ".dashboard-panel-header"
                ) ??
                this.elements.timeline.parentElement;

            header?.append(status);
            return status;
        }

        createCountElement() {
            const count = document.createElement("span");
            count.id = "event-stream-count";
            count.className = "event-stream-count";
            count.textContent = "0 events";
            this.elements.status?.insertAdjacentElement(
                "afterend",
                count
            );
            return count;
        }

        createUpdatedElement() {
            const updated = document.createElement("time");
            updated.id = "event-stream-updated";
            updated.className = "event-stream-updated";
            updated.textContent = "Not updated";
            this.elements.count?.insertAdjacentElement(
                "afterend",
                updated
            );
            return updated;
        }

        removePackPlaceholder() {
            const candidates = this.elements.panel?.querySelectorAll(
                ".empty-state, [data-placeholder], .pending-pack"
            ) ?? [];

            for (const candidate of candidates) {
                const text = normalizeString(candidate.textContent)
                    .toLowerCase();

                if (
                    text.includes("pending pack 4") ||
                    text.includes("event transport established") ||
                    text.includes("authoritative event retrieval")
                ) {
                    candidate.remove();
                }
            }
        }

        async refreshHistory({ force = false } = {}) {
            if (this.refreshPromise && !force) {
                return this.refreshPromise;
            }

            this.refreshPromise = this.performHistoryRefresh();

            try {
                return await this.refreshPromise;
            } finally {
                this.refreshPromise = null;
            }
        }

        async performHistoryRefresh() {
            const controller = new AbortController();
            const timeout = window.setTimeout(
                () => controller.abort(),
                CONFIGURATION.requestTimeoutMilliseconds
            );

            const endpoint = new URL(
                CONFIGURATION.restEndpoint,
                window.location.origin
            );
            endpoint.searchParams.set(
                "limit",
                String(CONFIGURATION.initialLimit)
            );

            try {
                const response = await window.fetch(endpoint, {
                    method: "GET",
                    headers: {
                        Accept: "application/json",
                    },
                    cache: "no-store",
                    credentials: "same-origin",
                    signal: controller.signal,
                });

                if (!response.ok) {
                    throw new Error(
                        `Executive event history returned HTTP ${response.status}.`
                    );
                }

                const envelope = await response.json();
                const events = envelope?.data?.events;

                if (!Array.isArray(events)) {
                    throw new Error(
                        "Executive event history contains no event array."
                    );
                }

                this.ingestEvents(events, {
                    replace: true,
                });

                this.updateTimestamp();
                return events;
            } catch (error) {
                this.setState(
                    EventState.DEGRADED,
                    error instanceof Error
                        ? error.message
                        : String(error)
                );
                this.renderEmptyState(
                    "Executive history unavailable",
                    error instanceof Error
                        ? error.message
                        : String(error)
                );
                return [];
            } finally {
                window.clearTimeout(timeout);
            }
        }

        connectLiveTransport() {
            if (this.stopped) {
                return;
            }

            this.clearReconnectTimer();

            const generation = ++this.socketGeneration;
            const scheme =
                window.location.protocol === "https:"
                    ? "wss:"
                    : "ws:";
            const url =
                `${scheme}//${window.location.host}` +
                CONFIGURATION.liveEndpoint;

            this.setState(
                EventState.CONNECTING,
                "Connecting to constitutional event stream"
            );

            try {
                this.socket = new WebSocket(url);
            } catch (error) {
                this.handleSocketFailure(generation, error);
                return;
            }

            this.socket.addEventListener("open", () => {
                if (generation !== this.socketGeneration) {
                    return;
                }

                this.reconnectAttempt = 0;
                this.stopPolling();
                this.setState(
                    EventState.LIVE,
                    "Live constitutional event stream"
                );
            });

            this.socket.addEventListener("message", (message) => {
                if (generation !== this.socketGeneration) {
                    return;
                }

                this.handleLiveMessage(message.data);
            });

            this.socket.addEventListener("error", () => {
                if (generation !== this.socketGeneration) {
                    return;
                }

                this.setState(
                    EventState.DEGRADED,
                    "Live event transport error"
                );
            });

            this.socket.addEventListener("close", () => {
                if (
                    generation !== this.socketGeneration ||
                    this.stopped
                ) {
                    return;
                }

                this.socket = null;
                this.startPolling();
                this.scheduleReconnect();
            });
        }

        handleLiveMessage(rawMessage) {
            let envelope;

            try {
                envelope = JSON.parse(rawMessage);
            } catch {
                return;
            }

            if (envelope?.message_type !== "executive.event") {
                return;
            }

            const event = envelope.payload;

            if (
                !event ||
                typeof event !== "object" ||
                !event.event_id
            ) {
                return;
            }

            this.ingestEvents([event], {
                replace: false,
            });
            this.updateTimestamp(envelope.published_at);
        }

        handleSocketFailure(generation, error) {
            if (generation !== this.socketGeneration) {
                return;
            }

            this.setState(
                EventState.DEGRADED,
                error instanceof Error
                    ? error.message
                    : "Unable to create WebSocket"
            );
            this.startPolling();
            this.scheduleReconnect();
        }

        scheduleReconnect() {
            if (this.stopped || this.reconnectTimer) {
                return;
            }

            const delay = Math.min(
                CONFIGURATION.reconnectMaximumMilliseconds,
                CONFIGURATION.reconnectBaseMilliseconds *
                    (2 ** this.reconnectAttempt)
            );
            this.reconnectAttempt += 1;

            this.reconnectTimer = window.setTimeout(() => {
                this.reconnectTimer = null;
                this.connectLiveTransport();
            }, delay);
        }

        clearReconnectTimer() {
            if (!this.reconnectTimer) {
                return;
            }

            window.clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        startPolling() {
            if (this.pollTimer || this.stopped) {
                return;
            }

            this.setState(
                EventState.POLLING,
                "Live stream unavailable; polling certified history"
            );

            this.pollTimer = window.setInterval(() => {
                void this.refreshHistory({
                    force: true,
                });
            }, CONFIGURATION.fallbackPollMilliseconds);
        }

        stopPolling() {
            if (!this.pollTimer) {
                return;
            }

            window.clearInterval(this.pollTimer);
            this.pollTimer = null;
        }

        ingestEvents(events, { replace }) {
            if (replace) {
                this.eventsById.clear();
            }

            for (const event of events) {
                const eventId = normalizeString(event?.event_id);

                if (!eventId) {
                    continue;
                }

                this.eventsById.set(eventId, event);
            }

            const ordered = [...this.eventsById.values()]
                .sort((left, right) => {
                    const leftSequence = Number(left.sequence ?? 0);
                    const rightSequence = Number(right.sequence ?? 0);

                    if (leftSequence !== rightSequence) {
                        return rightSequence - leftSequence;
                    }

                    return String(right.occurred_at ?? "")
                        .localeCompare(
                            String(left.occurred_at ?? "")
                        );
                })
                .slice(0, CONFIGURATION.maximumEvents);

            this.eventsById = new Map(
                ordered.map((event) => [
                    String(event.event_id),
                    event,
                ])
            );

            this.renderEvents(ordered);
            this.elements.count.textContent =
                `${ordered.length} ` +
                `${ordered.length === 1 ? "event" : "events"}`;

            this.application?.state.set(
                "executive.events",
                ordered,
                {
                    source: MODULE_NAME,
                }
            );
        }

        renderEvents(events) {
            this.elements.timeline.replaceChildren();

            if (events.length === 0) {
                this.renderEmptyState(
                    "No constitutional events",
                    "The Executive timeline is certified but currently empty."
                );
                return;
            }

            const fragment = document.createDocumentFragment();

            for (const event of events) {
                fragment.append(this.createEventElement(event));
            }

            this.elements.timeline.append(fragment);
        }

        createEventElement(event) {
            const kind = normalizeString(event.kind);
            const severity =
                SeverityByKind[kind] ?? "neutral";
            const timestamp = formatTimestamp(event.occurred_at);

            const article = document.createElement("article");
            article.className =
                `executive-event executive-event--${severity}`;
            article.dataset.eventId = normalizeString(event.event_id);
            article.dataset.eventKind = kind;
            article.dataset.subsystem =
                normalizeString(event.subsystem);

            const marker = document.createElement("span");
            marker.className =
                `executive-event-marker ` +
                `executive-event-marker--${severity}`;
            marker.setAttribute("aria-hidden", "true");

            const time = document.createElement("time");
            time.className = "executive-event-time";
            time.dateTime = timestamp.machine;
            time.textContent = timestamp.time;
            time.title = timestamp.full;

            const body = document.createElement("div");
            body.className = "executive-event-body";

            const header = document.createElement("div");
            header.className = "executive-event-heading";

            const title = document.createElement("strong");
            title.className = "executive-event-title";
            title.textContent =
                KindLabels[kind] ?? humanize(kind);

            const subsystem = document.createElement("span");
            subsystem.className = "executive-event-subsystem";
            subsystem.textContent =
                humanize(event.subsystem ?? "executive");

            header.append(title, subsystem);

            const summary = document.createElement("p");
            summary.className = "executive-event-summary";
            summary.textContent = this.eventSummary(event);

            const details = document.createElement("details");
            details.className = "executive-event-details";

            const detailSummary = document.createElement("summary");
            detailSummary.textContent = "Inspect event";

            const definitionList =
                document.createElement("dl");
            definitionList.className =
                "executive-event-metadata";

            this.appendMetadata(
                definitionList,
                "Sequence",
                event.sequence
            );
            this.appendMetadata(
                definitionList,
                "Event ID",
                event.event_id
            );
            this.appendMetadata(
                definitionList,
                "Mission",
                event.context?.mission_id
            );
            this.appendMetadata(
                definitionList,
                "Task",
                event.context?.task_id
            );
            this.appendMetadata(
                definitionList,
                "Correlation",
                event.context?.correlation_id
            );
            this.appendMetadata(
                definitionList,
                "Fingerprint",
                event.event_fingerprint
            );
            this.appendMetadata(
                definitionList,
                "Payload",
                event.payload
            );

            details.append(detailSummary, definitionList);
            body.append(header, summary, details);
            article.append(marker, time, body);

            return article;
        }

        eventSummary(event) {
            const payload = event?.payload ?? {};

            const preferredKeys = [
                "summary",
                "message",
                "detail",
                "error",
                "name",
                "component",
                "objective",
                "current_state",
                "legacy_event_type",
            ];

            for (const key of preferredKeys) {
                const value = payload[key];

                if (
                    value !== undefined &&
                    value !== null &&
                    value !== ""
                ) {
                    if (
                        key === "current_state" &&
                        payload.previous_state !== undefined
                    ) {
                        return (
                            `${humanize(payload.previous_state ?? "initial")} ` +
                            `→ ${humanize(value)}`
                        );
                    }

                    return escapeForDisplay(value);
                }
            }

            const missionId = event?.context?.mission_id;
            const taskId = event?.context?.task_id;

            if (taskId) {
                return `Task ${taskId}`;
            }

            if (missionId) {
                return `Mission ${missionId}`;
            }

            return "Constitutional Executive event committed.";
        }

        appendMetadata(list, label, value) {
            if (
                value === null ||
                value === undefined ||
                value === ""
            ) {
                return;
            }

            const term = document.createElement("dt");
            term.textContent = label;

            const description = document.createElement("dd");
            description.textContent = escapeForDisplay(value);

            list.append(term, description);
        }

        renderEmptyState(title, message) {
            this.elements.timeline.replaceChildren();

            const wrapper = document.createElement("div");
            wrapper.className =
                "empty-state executive-event-empty-state";

            const icon = document.createElement("span");
            icon.className = "empty-state-icon";
            icon.setAttribute("aria-hidden", "true");
            icon.textContent = "≋";

            const copy = document.createElement("div");
            const heading = document.createElement("strong");
            heading.textContent = title;

            const paragraph = document.createElement("p");
            paragraph.textContent = message;

            copy.append(heading, paragraph);
            wrapper.append(icon, copy);
            this.elements.timeline.append(wrapper);
        }

        setState(state, message) {
            if (!this.elements.status) {
                return;
            }

            this.elements.status.className =
                `event-stream-status event-stream-status--${state}`;
            this.elements.status.dataset.state = state;
            this.elements.status.textContent = humanize(state);
            this.elements.status.title = message;

            if (this.elements.panel) {
                this.elements.panel.dataset.streamState = state;
            }
        }

        updateTimestamp(value = new Date().toISOString()) {
            const timestamp = formatTimestamp(value);
            this.elements.updated.dateTime = timestamp.machine;
            this.elements.updated.textContent =
                `Updated ${timestamp.time}`;
            this.elements.updated.title = timestamp.full;
        }

        stop() {
            this.stopped = true;
            this.clearReconnectTimer();
            this.stopPolling();

            if (this.socket) {
                this.socketGeneration += 1;
                this.socket.close();
                this.socket = null;
            }

            this.setState(
                EventState.STOPPED,
                "Executive event projection stopped"
            );
        }
    }

    const registerProjection = () => {
        if (
            !window.JARVIS ||
            typeof window.JARVIS.registerController !== "function"
        ) {
            console.error(
                "[Executive Event Timeline] JARVIS runtime unavailable."
            );
            return;
        }

        try {
            window.JARVIS.registerController(
                MODULE_NAME,
                new ExecutiveEventTimelineProjection()
            );

            /* Callable workspace: history, websocket, and fallback polling
               start only when Timeline is requested. */
        } catch (error) {
            window.JARVIS.reportError(error, {
                source: MODULE_NAME,
                fatal: false,
            });
        }
    };

    window.JARVIS_EVENT_TIMELINE = Object.freeze({
        version: MODULE_VERSION,
        moduleName: MODULE_NAME,
        configuration: CONFIGURATION,
    });

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            registerProjection,
            { once: true }
        );
    } else {
        registerProjection();
    }
})();
