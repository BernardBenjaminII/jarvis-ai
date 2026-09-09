/* =============================================================================
   GENESIS VII-A0 — PACK 3B-2.2
   EXECUTIVE HEALTH AND RUNTIME PROJECTION
   ============================================================================= */

"use strict";

(() => {
    const MODULE_NAME = "executiveHealthRuntimeProjection";
    const MODULE_VERSION = "Genesis VII-A0 Pack 3B-2.2";

    const HealthStates = Object.freeze([
        "healthy",
        "degraded",
        "critical",
        "unavailable",
        "unknown",
    ]);

    const MetricStates = Object.freeze([
        "available",
        "not_configured",
        "unavailable",
    ]);

    const HealthLabels = Object.freeze({
        healthy: "Healthy",
        degraded: "Degraded",
        critical: "Critical",
        unavailable: "Unavailable",
        unknown: "Unknown",
    });

    const HealthSymbols = Object.freeze({
        healthy: "✓",
        degraded: "!",
        critical: "×",
        unavailable: "—",
        unknown: "◌",
    });

    const MetricLabels = Object.freeze({
        available: "Available",
        not_configured: "Not configured",
        unavailable: "Unavailable",
    });

    const nowIso = () => new Date().toISOString();

    const normalizeState = (
        value,
        supportedStates,
        fallback
    ) => {
        const normalized = String(value ?? "")
            .trim()
            .toLowerCase()
            .replace(/\s+/g, "_")
            .replace(/-/g, "_");

        return supportedStates.includes(normalized)
            ? normalized
            : fallback;
    };

    const escapeText = (value) => String(value ?? "");

    const formatNumber = (value) => {
        const numeric = Number(value);

        if (!Number.isFinite(numeric)) {
            return "—";
        }

        return new Intl.NumberFormat().format(numeric);
    };

    const formatPercent = (value) => {
        const numeric = Number(value);

        if (!Number.isFinite(numeric)) {
            return "—";
        }

        return `${numeric.toFixed(2)}%`;
    };

    const formatBytes = (bytes) => {
        const numeric = Number(bytes);

        if (!Number.isFinite(numeric) || numeric < 0) {
            return null;
        }

        const units = [
            "B",
            "KiB",
            "MiB",
            "GiB",
            "TiB",
            "PiB",
        ];

        let value = numeric;
        let unitIndex = 0;

        while (
            value >= 1024 &&
            unitIndex < units.length - 1
        ) {
            value /= 1024;
            unitIndex += 1;
        }

        const precision = value >= 10 ? 1 : 2;

        return `${value.toFixed(precision)} ${units[unitIndex]}`;
    };

    const extractFreeBytes = (message) => {
        const match = String(message ?? "").match(
            /(\d+)\s+bytes\s+free/i
        );

        if (!match) {
            return null;
        }

        return Number(match[1]);
    };

    const formatTimestamp = (value) => {
        if (!value) {
            return {
                machine: "",
                display: "Not yet updated",
            };
        }

        const timestamp = new Date(value);

        if (Number.isNaN(timestamp.getTime())) {
            return {
                machine: "",
                display: "Timestamp unavailable",
            };
        }

        return {
            machine: timestamp.toISOString(),
            display: timestamp.toLocaleString([], {
                year: "numeric",
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
            }),
        };
    };

    class ExecutiveHealthRuntimeProjection {
        constructor() {
            this.application = null;
            this.unsubscribers = [];
            this.refreshPromise = null;
            this.lastDashboard = null;
            this.elements = {};
        }

        async initialize(application) {
            this.application = application;
            this.cacheElements();

            application.state.set(
                "runtime.healthRuntimeProjection",
                {
                    state: "ready",
                    version: MODULE_VERSION,
                    initializedAt: nowIso(),
                },
                {
                    source: MODULE_NAME,
                }
            );

            const refreshEvent =
                window.JARVIS?.runtimeEvents?.REFRESH_REQUESTED;

            if (refreshEvent) {
                this.unsubscribers.push(
                    application.events.on(
                        refreshEvent,
                        ({ source = "runtime" }) => {
                            void this.refresh({
                                forceRefresh: true,
                                source,
                            });
                        }
                    )
                );
            }

            const dashboardSuccessEvent =
                window.JARVIS_DASHBOARD?.events
                    ?.REFRESH_SUCCEEDED;

            if (dashboardSuccessEvent) {
                this.unsubscribers.push(
                    application.events.on(
                        dashboardSuccessEvent,
                        ({ status }) => {
                            if (
                                this.lastDashboard &&
                                status
                            ) {
                                this.lastDashboard.status = status;
                                this.projectAttention(status);
                            }
                        }
                    )
                );
            }

            await this.refresh({
                forceRefresh: false,
                source: "health-runtime-initialization",
            });
        }

        cacheElements() {
            const selectors = {
                healthPanel: "#executive-health-panel",
                healthState: "#executive-health-state",
                healthChecks: "#executive-health-checks",
                healthUpdated: "#health-panel-updated",

                attentionPanel: "#executive-attention-panel",
                attentionCount: "#attention-item-count",
                attentionList: "#executive-attention-list",

                runtimePython: "#runtime-python-version",
                runtimeCpus: "#runtime-logical-cpus",
                runtimeLoad: "#runtime-system-load",
                runtimeMemory: "#runtime-memory",
                runtimeSource: "#runtime-source-label",

                projectStoragePercent:
                    "#storage-project-percent",
                projectStorageBar:
                    "#storage-project-bar",
                rootStoragePercent:
                    "#storage-root-percent",
                rootStorageBar:
                    "#storage-root-bar",

                metricSourceSummary:
                    "#metric-source-summary",

                navigationMissionCount:
                    "#navigation-mission-count",

                workstreamMission:
                    "#workstream-mission-summary",
                workstreamKnowledge:
                    "#workstream-knowledge-summary",
                workstreamAi:
                    "#workstream-ai-summary",
                workstreamRobotics:
                    "#workstream-robotics-summary",
            };

            for (const [name, selector] of Object.entries(selectors)) {
                this.elements[name] =
                    document.querySelector(selector);
            }
        }

        async refresh({
            forceRefresh = false,
            source = "unknown",
        } = {}) {
            if (this.refreshPromise) {
                return this.refreshPromise;
            }

            this.refreshPromise = this.performRefresh({
                forceRefresh,
                source,
            });

            try {
                return await this.refreshPromise;
            } finally {
                this.refreshPromise = null;
            }
        }

        async performRefresh({
            forceRefresh,
            source,
        }) {
            if (
                !window.JARVIS_API ||
                typeof window.JARVIS_API.dashboard !==
                    "function"
            ) {
                this.projectUnavailable(
                    "Executive API client unavailable."
                );
                return null;
            }

            try {
                const envelope =
                    await window.JARVIS_API.dashboard({
                        refresh: forceRefresh,
                        timeoutMilliseconds: 30000,
                        retryAttempts: 0,
                        handleTimeoutLocally: true,
                    });

                const dashboard =
                    this.validateDashboard(envelope);

                this.lastDashboard = dashboard;

                this.projectDashboard(dashboard);

                this.application.state.set(
                    "dashboard.health",
                    dashboard.health,
                    {
                        source: MODULE_NAME,
                        requestSource: source,
                    }
                );

                this.application.state.set(
                    "dashboard.metrics",
                    dashboard.metrics,
                    {
                        source: MODULE_NAME,
                        requestSource: source,
                    }
                );

                this.application.state.set(
                    "dashboard.attentionItems",
                    dashboard.status?.attention_items ?? [],
                    {
                        source: MODULE_NAME,
                        requestSource: source,
                    }
                );

                return dashboard;
            } catch (error) {
                this.projectUnavailable(
                    error instanceof Error
                        ? error.message
                        : String(error)
                );

                return null;
            }
        }

        validateDashboard(envelope) {
            if (!envelope || typeof envelope !== "object") {
                throw new Error(
                    "Executive dashboard response is invalid."
                );
            }

            if (!envelope.data || typeof envelope.data !== "object") {
                throw new Error(
                    "Executive dashboard response contains no data."
                );
            }

            const dashboard = envelope.data;

            if (
                !dashboard.health ||
                typeof dashboard.health !== "object"
            ) {
                throw new Error(
                    "Executive dashboard contains no health model."
                );
            }

            if (
                !dashboard.metrics ||
                typeof dashboard.metrics !== "object"
            ) {
                throw new Error(
                    "Executive dashboard contains no metrics model."
                );
            }

            if (
                !dashboard.status ||
                typeof dashboard.status !== "object"
            ) {
                throw new Error(
                    "Executive dashboard contains no status model."
                );
            }

            return dashboard;
        }

        projectDashboard(dashboard) {
            this.projectHealth(dashboard.health);
            this.projectAttention(dashboard.status);
            this.projectRuntime(
                dashboard.health,
                dashboard.metrics
            );
            this.projectStorage(dashboard.health);
            this.projectMetricCards(dashboard.metrics);
            this.projectWorkstreams(dashboard.metrics);

            const timestamp = formatTimestamp(
                dashboard.generated_at ??
                dashboard.health.generated_at ??
                dashboard.metrics.generated_at
            );

            if (this.elements.healthUpdated) {
                this.elements.healthUpdated.textContent =
                    timestamp.display;
                this.elements.healthUpdated.dateTime =
                    timestamp.machine;
            }
        }

        projectHealth(health) {
            const overallState = normalizeState(
                health.overall_state,
                HealthStates,
                "unknown"
            );

            if (this.elements.healthState) {
                this.elements.healthState.className =
                    `state-pill state-pill--${overallState}`;

                this.elements.healthState.textContent =
                    HealthLabels[overallState];
            }

            if (this.elements.healthPanel) {
                this.elements.healthPanel.dataset.state =
                    overallState;
            }

            const checks = Array.isArray(health.checks)
                ? health.checks
                : [];

            if (!this.elements.healthChecks) {
                return;
            }

            this.elements.healthChecks.replaceChildren();

            if (checks.length === 0) {
                this.elements.healthChecks.append(
                    this.createEmptyState(
                        "No health checks available",
                        "The Executive Health service returned no checks."
                    )
                );

                return;
            }

            for (const check of checks) {
                this.elements.healthChecks.append(
                    this.createHealthCheck(check)
                );
            }
        }

        createHealthCheck(check) {
            const state = normalizeState(
                check.state,
                HealthStates,
                "unknown"
            );

            const item = document.createElement("div");
            item.className = "health-check-item";
            item.dataset.state = state;
            item.setAttribute("role", "listitem");

            const indicator = document.createElement("span");
            indicator.className =
                `status-indicator status-indicator--${state}`;
            indicator.setAttribute("aria-hidden", "true");

            const copy = document.createElement("div");

            const name = document.createElement("div");
            name.className = "health-check-item-name";
            name.textContent =
                escapeText(check.name || check.identifier);

            const message = document.createElement("div");
            message.className = "health-check-item-message";
            message.textContent = this.healthCheckMessage(check);

            copy.append(name, message);

            const value = document.createElement("div");
            value.className = "health-check-item-value";
            value.textContent = this.healthCheckValue(check);

            item.append(indicator, copy, value);

            return item;
        }

        healthCheckMessage(check) {
            const message = String(check.message ?? "").trim();

            if (message) {
                const freeBytes = extractFreeBytes(message);

                if (freeBytes !== null) {
                    return message.replace(
                        /\d+\s+bytes\s+free/i,
                        `${formatBytes(freeBytes)} free`
                    );
                }

                return message;
            }

            return HealthLabels[
                normalizeState(
                    check.state,
                    HealthStates,
                    "unknown"
                )
            ];
        }

        healthCheckValue(check) {
            if (
                check.unit === "percent" &&
                Number.isFinite(Number(check.observed_value))
            ) {
                return formatPercent(check.observed_value);
            }

            if (
                check.observed_value &&
                typeof check.observed_value === "object"
            ) {
                const observed = check.observed_value;

                if (
                    Object.prototype.hasOwnProperty.call(
                        observed,
                        "one_minute"
                    )
                ) {
                    return formatNumber(
                        observed.one_minute
                    );
                }

                return "Observed";
            }

            if (
                check.observed_value === null ||
                check.observed_value === undefined ||
                check.observed_value === ""
            ) {
                return "—";
            }

            return escapeText(check.observed_value);
        }

        projectAttention(status) {
            const attentionItems = Array.isArray(
                status?.attention_items
            )
                ? status.attention_items
                : [];

            if (this.elements.attentionCount) {
                this.elements.attentionCount.textContent =
                    formatNumber(attentionItems.length);
            }

            if (!this.elements.attentionList) {
                return;
            }

            this.elements.attentionList.replaceChildren();

            if (attentionItems.length === 0) {
                this.elements.attentionList.append(
                    this.createEmptyState(
                        "No immediate attention required",
                        "Connected Executive systems report no active deficiencies."
                    )
                );

                return;
            }

            for (const attention of attentionItems) {
                const item = document.createElement("div");
                item.className = "attention-item";

                const indicator = document.createElement("span");
                indicator.className =
                    "status-indicator status-indicator--degraded";
                indicator.setAttribute("aria-hidden", "true");

                const copy = document.createElement("div");

                const title = document.createElement("div");
                title.className = "attention-item-title";
                title.textContent =
                    this.attentionTitle(attention);

                const message = document.createElement("div");
                message.className = "attention-item-message";
                message.textContent =
                    this.attentionMessage(attention);

                copy.append(title, message);

                const severity = document.createElement("span");
                severity.className =
                    "state-pill state-pill--degraded";
                severity.textContent = "Attention";

                item.append(indicator, copy, severity);
                this.elements.attentionList.append(item);
            }
        }

        attentionTitle(attention) {
            const text = String(attention ?? "").trim();
            const separator = text.indexOf(":");

            if (separator > 0) {
                return text.slice(0, separator).trim();
            }

            return "Executive condition";
        }

        attentionMessage(attention) {
            const text = String(attention ?? "").trim();
            const separator = text.indexOf(":");

            const message = separator > 0
                ? text.slice(separator + 1).trim()
                : text;

            const freeBytes = extractFreeBytes(message);

            if (freeBytes === null) {
                return message;
            }

            return message.replace(
                /\d+\s+bytes\s+free/i,
                `${formatBytes(freeBytes)} free`
            );
        }

        projectRuntime(health, metrics) {
            const checks = this.checkMap(health);
            const metricValues = this.metricMap(metrics);

            const python = checks.get("python_runtime");
            const load = checks.get("system_load");
            const memory = checks.get("memory");
            const cpus = metricValues.get("logical_cpus");

            this.setText(
                this.elements.runtimePython,
                python?.observed_value ?? "—"
            );

            this.setText(
                this.elements.runtimeCpus,
                cpus?.state === "available"
                    ? formatNumber(cpus.value)
                    : "—"
            );

            this.setText(
                this.elements.runtimeLoad,
                this.formatLoad(load?.observed_value)
            );

            this.setText(
                this.elements.runtimeMemory,
                this.formatMemory(memory)
            );

            this.setText(
                this.elements.runtimeSource,
                python?.message ||
                "Executive Health telemetry"
            );
        }

        formatLoad(observedValue) {
            if (
                !observedValue ||
                typeof observedValue !== "object"
            ) {
                return "—";
            }

            const one = Number(observedValue.one_minute);
            const five = Number(observedValue.five_minutes);
            const fifteen = Number(
                observedValue.fifteen_minutes
            );

            if (
                !Number.isFinite(one) ||
                !Number.isFinite(five) ||
                !Number.isFinite(fifteen)
            ) {
                return "—";
            }

            return [
                one.toFixed(2),
                five.toFixed(2),
                fifteen.toFixed(2),
            ].join(" / ");
        }

        formatMemory(memoryCheck) {
            if (!memoryCheck) {
                return "—";
            }

            const usedPercent = Number(
                memoryCheck.observed_value
            );

            const match = String(
                memoryCheck.message ?? ""
            ).match(
                /(\d+)\s+KiB\s+available\s+of\s+(\d+)\s+KiB/i
            );

            if (match) {
                const availableBytes =
                    Number(match[1]) * 1024;

                const totalBytes =
                    Number(match[2]) * 1024;

                return (
                    `${formatBytes(availableBytes)} available ` +
                    `of ${formatBytes(totalBytes)}`
                );
            }

            if (Number.isFinite(usedPercent)) {
                return `${formatPercent(usedPercent)} used`;
            }

            return "—";
        }

        projectStorage(health) {
            const checks = this.checkMap(health);

            this.projectStorageCheck(
                checks.get("project_disk"),
                this.elements.projectStoragePercent,
                this.elements.projectStorageBar
            );

            this.projectStorageCheck(
                checks.get("root_disk"),
                this.elements.rootStoragePercent,
                this.elements.rootStorageBar
            );
        }

        projectStorageCheck(
            check,
            percentageElement,
            barElement
        ) {
            const value = Number(check?.observed_value);
            const percent = Number.isFinite(value)
                ? Math.max(0, Math.min(100, value))
                : 0;

            this.setText(
                percentageElement,
                Number.isFinite(value)
                    ? formatPercent(value)
                    : "—"
            );

            if (!barElement) {
                return;
            }

            barElement.style.width = `${percent}%`;

            const track = barElement.parentElement;

            if (track) {
                track.setAttribute(
                    "aria-valuenow",
                    String(Math.round(percent))
                );

                track.dataset.state =
                    percent >= 95
                        ? "critical"
                        : percent >= 85
                            ? "warning"
                            : "healthy";
            }
        }

        projectMetricCards(metrics) {
            const metricValues = this.metricMap(metrics);

            for (
                const [identifier, metric]
                of metricValues.entries()
            ) {
                const valueElement = document.querySelector(
                    `[data-metric-value="${identifier}"]`
                );

                const stateElement = document.querySelector(
                    `[data-metric-state="${identifier}"]`
                );

                const card = document.querySelector(
                    `[data-metric-card="${identifier}"]`
                );

                const state = normalizeState(
                    metric.state,
                    MetricStates,
                    "unavailable"
                );

                if (valueElement) {
                    valueElement.textContent =
                        state === "available"
                            ? formatNumber(metric.value)
                            : "—";
                }

                if (stateElement) {
                    stateElement.textContent =
                        state === "available"
                            ? MetricLabels.available
                            : MetricLabels[state];
                }

                if (card) {
                    card.dataset.state = state;
                }
            }

            const available = [...metricValues.values()]
                .filter(
                    (metric) =>
                        metric.state === "available"
                )
                .length;

            const total = metricValues.size;

            this.setText(
                this.elements.metricSourceSummary,
                `${available} of ${total} metric sources available`
            );

            const mission = metricValues.get("missions");

            if (this.elements.navigationMissionCount) {
                this.elements.navigationMissionCount.textContent =
                    mission?.state === "available"
                        ? formatNumber(mission.value)
                        : "—";

                this.elements.navigationMissionCount.setAttribute(
                    "aria-label",
                    mission?.state === "available"
                        ? `${formatNumber(mission.value)} missions`
                        : "Mission registry not configured"
                );
            }
        }

        projectWorkstreams(metrics) {
            const metricValues = this.metricMap(metrics);

            this.setText(
                this.elements.workstreamMission,
                this.metricWorkstreamSummary(
                    metricValues.get("missions")
                )
            );

            this.setText(
                this.elements.workstreamKnowledge,
                this.metricWorkstreamSummary(
                    metricValues.get("knowledge_files"),
                    "knowledge files"
                )
            );

            this.setText(
                this.elements.workstreamAi,
                this.metricWorkstreamSummary(
                    metricValues.get("ai_models"),
                    "AI models"
                )
            );

            this.setText(
                this.elements.workstreamRobotics,
                this.metricWorkstreamSummary(
                    metricValues.get("robots"),
                    "robots"
                )
            );
        }

        metricWorkstreamSummary(metric, suffix = "records") {
            if (!metric) {
                return "Metric unavailable";
            }

            if (metric.state === "available") {
                return `${formatNumber(metric.value)} ${suffix}`;
            }

            if (metric.state === "not_configured") {
                return "Registry not configured";
            }

            return "Authoritative source unavailable";
        }

        metricMap(metrics) {
            const values =
                metrics?.metrics &&
                typeof metrics.metrics === "object"
                    ? metrics.metrics
                    : {};

            return new Map(Object.entries(values));
        }

        checkMap(health) {
            const checks = Array.isArray(health?.checks)
                ? health.checks
                : [];

            return new Map(
                checks.map(
                    (check) => [
                        String(check.identifier),
                        check,
                    ]
                )
            );
        }

        createEmptyState(title, message) {
            const wrapper = document.createElement("div");
            wrapper.className =
                "empty-state empty-state--compact";

            const icon = document.createElement("span");
            icon.className = "empty-state-icon";
            icon.setAttribute("aria-hidden", "true");
            icon.textContent = "◌";

            const copy = document.createElement("div");

            const heading = document.createElement("strong");
            heading.textContent = title;

            const description = document.createElement("p");
            description.textContent = message;

            copy.append(heading, description);
            wrapper.append(icon, copy);

            return wrapper;
        }

        projectUnavailable(message) {
            if (this.elements.healthState) {
                this.elements.healthState.className =
                    "state-pill state-pill--unavailable";
                this.elements.healthState.textContent =
                    "Unavailable";
            }

            if (this.elements.healthChecks) {
                this.elements.healthChecks.replaceChildren(
                    this.createEmptyState(
                        "Health telemetry unavailable",
                        message
                    )
                );
            }

            if (this.elements.attentionCount) {
                this.elements.attentionCount.textContent = "—";
            }

            if (this.elements.attentionList) {
                this.elements.attentionList.replaceChildren(
                    this.createEmptyState(
                        "Assessment unavailable",
                        message
                    )
                );
            }

            this.setText(this.elements.runtimePython, "—");
            this.setText(this.elements.runtimeCpus, "—");
            this.setText(this.elements.runtimeLoad, "—");
            this.setText(this.elements.runtimeMemory, "—");
            this.setText(
                this.elements.runtimeSource,
                "Telemetry unavailable"
            );
        }

        setText(element, value) {
            if (element) {
                element.textContent = escapeText(value);
            }
        }

        stop() {
            for (const unsubscribe of this.unsubscribers) {
                unsubscribe();
            }

            this.unsubscribers = [];
        }
    }

    const registerProjection = () => {
        if (
            !window.JARVIS ||
            typeof window.JARVIS.registerController !==
                "function"
        ) {
            console.error(
                "[Executive Health Projection] " +
                "JARVIS runtime unavailable."
            );
            return;
        }

        try {
            window.JARVIS.registerController(
                MODULE_NAME,
                new ExecutiveHealthRuntimeProjection()
            );

            /* Callable workspace: defer the 30-second dashboard request. */
        } catch (error) {
            window.JARVIS.reportError(
                error,
                {
                    source:
                        "executive-health-runtime-projection",
                    fatal: false,
                }
            );
        }
    };

    window.JARVIS_HEALTH_PROJECTION = Object.freeze({
        version: MODULE_VERSION,
        moduleName: MODULE_NAME,
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
