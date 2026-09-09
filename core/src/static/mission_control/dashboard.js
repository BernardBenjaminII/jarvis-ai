/* =============================================================================
   GENESIS VII-A0 — PACK 3B-2.1
   EXECUTIVE STATUS BANNER PROJECTION
   ============================================================================= */

"use strict";

(() => {
    const RuntimeEvents =
    window.JARVIS?.runtimeEvents ?? {};
    const CONTROLLER_NAME = "dashboardStatusProjection";
    const CONTROLLER_VERSION = "Genesis VII-A0 Pack 3B-2.1";

    const DashboardEvents = Object.freeze({
        REFRESH_STARTED: "executive:dashboard-refresh-started",
        REFRESH_SUCCEEDED: "executive:dashboard-refresh-succeeded",
        REFRESH_FAILED: "executive:dashboard-refresh-failed",
        STATUS_PROJECTED: "executive:dashboard-status-projected",
    });

    const SupportedStatusStates = Object.freeze([
        "excellent",
        "operational",
        "degraded",
        "critical",
        "unknown",
    ]);

    const SupportedHealthStates = Object.freeze([
        "healthy",
        "degraded",
        "critical",
        "unavailable",
        "unknown",
    ]);

    const StatusSymbols = Object.freeze({
        excellent: "✓",
        operational: "●",
        degraded: "!",
        critical: "×",
        unknown: "◌",
    });

    const StatusLabels = Object.freeze({
        excellent: "Excellent",
        operational: "Operational",
        degraded: "Degraded",
        critical: "Critical",
        unknown: "Unknown",
    });

    const HealthLabels = Object.freeze({
        healthy: "Healthy",
        degraded: "Degraded",
        critical: "Critical",
        unavailable: "Unavailable",
        unknown: "Unknown",
    });

    const nowIso = () => new Date().toISOString();

    const normalizeState = (
        value,
        supportedStates,
        fallback = "unknown"
    ) => {
        const normalized = String(value ?? "")
            .trim()
            .toLowerCase()
            .replace(/\s+/g, "_");

        return supportedStates.includes(normalized)
            ? normalized
            : fallback;
    };

    const formatTimestamp = (value) => {
        if (!value) {
            return {
                machine: "",
                display: "Awaiting data",
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

    const formatMetricSummary = (status) => {
        const available = Number(status.available_metrics ?? 0);
        const configured = Number(status.configured_metrics ?? 0);
        const unavailable = Number(status.unavailable_metrics ?? 0);

        if (
            !Number.isFinite(available) ||
            !Number.isFinite(configured) ||
            !Number.isFinite(unavailable)
        ) {
            return "Unavailable";
        }

        if (configured === 0) {
            return "0 configured";
        }

        if (unavailable > 0) {
            return `${available}/${configured} available`;
        }

        return `${available} available`;
    };

    class ExecutiveStatusBannerProjection {
        constructor() {
            this.application = null;
            this.refreshInProgress = null;
            this.unsubscribers = [];
            this.elements = {};
        }

        async initialize(application) {
            this.application = application;
            this.cacheElements();

            application.state.set(
                "runtime.dashboardStatusProjection",
                {
                    state: "ready",
                    version: CONTROLLER_VERSION,
                    initializedAt: nowIso(),
                },
                {
                    source: CONTROLLER_NAME,
                }
            );

            this.unsubscribers.push(
                application.events.on(
                    RuntimeEvents.REFRESH_REQUESTED,
                    ({ source = "runtime" }) => {
                        void this.refresh({
                            forceRefresh: true,
                            source
                        });
                    }
                )
            );

            if (
                window.JARVIS_API &&
                window.JARVIS_API.events &&
                window.JARVIS_API.events.CLIENT_READY
            ) {
                this.unsubscribers.push(
                    application.events.on(
                        window.JARVIS_API.events.CLIENT_READY,
                        () => {
                            void this.refresh({
                                forceRefresh: false,
                                source: "api-client-ready",
                            });
                        }
                    )
                );
            }

            await this.refresh({
                forceRefresh: false,
                source: "controller-initialization",
            });
        }

        cacheElements() {
            const selectors = {
                banner: "#executive-status-banner",
                symbol: "#executive-status-symbol",
                heading: "#executive-status-heading",
                message: "#executive-status-message",
                health: "#status-banner-health",
                metrics: "#status-banner-metrics",
                updated: "#status-banner-updated",
                statusBarHealth: "#status-bar-health",
                statusBarUpdated: "#status-bar-last-update",
            };

            for (const [name, selector] of Object.entries(selectors)) {
                const element = document.querySelector(selector);

                if (!element) {
                    throw new Error(
                        `Status projection element '${name}' was not found: ` +
                        selector
                    );
                }

                this.elements[name] = element;
            }
        }

        validateDashboardEnvelope(envelope) {
            if (!envelope || typeof envelope !== "object") {
                throw new Error(
                    "Executive dashboard response is not an object."
                );
            }

            if (
                !envelope.data ||
                typeof envelope.data !== "object"
            ) {
                throw new Error(
                    "Executive dashboard response contains no data."
                );
            }

            if (
                !envelope.data.status ||
                typeof envelope.data.status !== "object"
            ) {
                throw new Error(
                    "Executive dashboard response contains no status."
                );
            }

            return envelope.data;
        }

        async refresh({
            forceRefresh = false,
            source = "unknown",
        } = {}) {
            if (this.refreshInProgress) {
                return this.refreshInProgress;
            }

            this.refreshInProgress = this.performRefresh({
                forceRefresh,
                source,
            });

            try {
                return await this.refreshInProgress;
            } finally {
                this.refreshInProgress = null;
            }
        }

        async performRefresh({
            forceRefresh,
            source,
        }) {
            if (
                !window.JARVIS_API ||
                typeof window.JARVIS_API.dashboard !== "function"
            ) {
                this.projectUnavailable(
                    "Executive API client is unavailable."
                );

                return null;
            }

            const startedAt = nowIso();

            this.application.events.emit(
                DashboardEvents.REFRESH_STARTED,
                {
                    source,
                    forceRefresh,
                    startedAt,
                }
            );

            try {
                const envelope = await window.JARVIS_API.dashboard({
                    refresh: forceRefresh,
                    timeoutMilliseconds: 30000,
                });

                const dashboard = this.validateDashboardEnvelope(
                    envelope
                );

                this.projectStatus(
                    dashboard.status,
                    dashboard.generated_at
                );

                this.application.state.set(
                    "dashboard.status",
                    dashboard.status,
                    {
                        source: CONTROLLER_NAME,
                    }
                );

                this.application.state.set(
                    "dashboard.lastUpdatedAt",
                    dashboard.generated_at ?? nowIso(),
                    {
                        source: CONTROLLER_NAME,
                    }
                );

                this.application.setHealthState(
                    normalizeState(
                        dashboard.status.health_state,
                        SupportedHealthStates
                    ),
                    {
                        source: CONTROLLER_NAME,
                    }
                );

                this.application.setConnectionState(
                    "connected",
                    {
                        source: CONTROLLER_NAME,
                        transport: "rest",
                    }
                );

                this.application.events.emit(
                    DashboardEvents.REFRESH_SUCCEEDED,
                    {
                        source,
                        forceRefresh,
                        startedAt,
                        completedAt: nowIso(),
                        status: dashboard.status,
                    }
                );

                return dashboard;
            } catch (error) {
                this.application.setConnectionState(
                    "degraded",
                    {
                        source: CONTROLLER_NAME,
                        reason:
                            error instanceof Error
                                ? error.message
                                : String(error),
                    }
                );

                this.projectFailure(error);

                this.application.events.emit(
                    DashboardEvents.REFRESH_FAILED,
                    {
                        source,
                        forceRefresh,
                        startedAt,
                        failedAt: nowIso(),
                        message:
                            error instanceof Error
                                ? error.message
                                : String(error),
                    }
                );

                return null;
            }
        }

        projectStatus(status, dashboardGeneratedAt = null) {
            const overallState = normalizeState(
                status.overall_state,
                SupportedStatusStates
            );

            const healthState = normalizeState(
                status.health_state,
                SupportedHealthStates
            );

            const headline =
                String(status.headline ?? "").trim() ||
                "Executive operating status available";

            const attentionItems = Array.isArray(
                status.attention_items
            )
                ? status.attention_items
                : [];

            const message = attentionItems.length > 0
                ? attentionItems[0]
                : this.defaultMessage(overallState);

            const generatedAt =
                status.generated_at ??
                dashboardGeneratedAt ??
                nowIso();

            const timestamp = formatTimestamp(generatedAt);
            const metricSummary = formatMetricSummary(status);

            this.elements.banner.className =
                `executive-status-banner ` +
                `executive-status-banner--${overallState}`;

            this.elements.banner.dataset.state = overallState;
            this.elements.banner.dataset.healthState = healthState;

            this.elements.symbol.textContent =
                StatusSymbols[overallState];

            this.elements.heading.textContent = headline;
            this.elements.message.textContent = message;

            this.elements.health.textContent =
                HealthLabels[healthState];

            this.elements.metrics.textContent = metricSummary;

            this.elements.updated.textContent = timestamp.display;
            this.elements.updated.dateTime = timestamp.machine;

            this.elements.statusBarHealth.textContent =
                `Health ${HealthLabels[healthState].toLowerCase()}`;

            this.elements.statusBarUpdated.textContent =
                `Updated ${timestamp.display}`;

            this.application.announce(
                `Executive status ${StatusLabels[overallState]}. ` +
                headline
            );

            this.application.events.emit(
                DashboardEvents.STATUS_PROJECTED,
                {
                    overallState,
                    healthState,
                    headline,
                    message,
                    generatedAt: timestamp.machine,
                }
            );
        }

        defaultMessage(overallState) {
            const messages = {
                excellent:
                    "All connected Executive systems report normal operation.",

                operational:
                    "Executive operations are available.",

                degraded:
                    "Executive operations remain available with deficiencies.",

                critical:
                    "Executive intervention is required.",

                unknown:
                    "Executive status could not be fully determined.",
            };

            return messages[overallState] ?? messages.unknown;
        }

        projectUnavailable(message) {
            this.elements.banner.className =
                "executive-status-banner " +
                "executive-status-banner--unknown";

            this.elements.banner.dataset.state = "unknown";

            this.elements.symbol.textContent = StatusSymbols.unknown;

            this.elements.heading.textContent =
                "Executive status unavailable";

            this.elements.message.textContent = message;

            this.elements.health.textContent = "Unknown";
            this.elements.metrics.textContent = "Unavailable";
            this.elements.updated.textContent = "Awaiting data";
            this.elements.updated.dateTime = "";

            this.elements.statusBarHealth.textContent =
                "Health unknown";

            this.elements.statusBarUpdated.textContent =
                "No live update received";
        }

        projectFailure(error) {
            const message =
                error instanceof Error
                    ? error.message
                    : String(error);

            this.elements.banner.className =
                "executive-status-banner " +
                "executive-status-banner--degraded";

            this.elements.banner.dataset.state = "degraded";

            this.elements.symbol.textContent =
                StatusSymbols.degraded;

            this.elements.heading.textContent =
                "Executive status retrieval failed";

            this.elements.message.textContent = message;

            this.elements.health.textContent = "Unavailable";
            this.elements.metrics.textContent = "Unavailable";

            const timestamp = formatTimestamp(nowIso());

            this.elements.updated.textContent = timestamp.display;
            this.elements.updated.dateTime = timestamp.machine;

            this.elements.statusBarHealth.textContent =
                "Health unavailable";

            this.elements.statusBarUpdated.textContent =
                "Dashboard refresh failed";
        }

        stop() {
            for (const unsubscribe of this.unsubscribers) {
                unsubscribe();
            }

            this.unsubscribers = [];
        }
    }

    const registerController = () => {
        if (
            !window.JARVIS ||
            typeof window.JARVIS.registerController !== "function"
        ) {
            console.error(
                "[Executive Dashboard] JARVIS runtime is unavailable."
            );

            return;
        }

        try {
            window.JARVIS.registerController(
                CONTROLLER_NAME,
                new ExecutiveStatusBannerProjection()
            );

            /* Callable workspace: registration is cheap; initialization and
               network retrieval occur only when the operator opens Operations. */
        } catch (error) {
            window.JARVIS.reportError(
                error,
                {
                    source: "dashboard-status-registration",
                    fatal: false,
                }
            );
        }
    };

    window.JARVIS_DASHBOARD = Object.freeze({
        version: CONTROLLER_VERSION,
        events: DashboardEvents,
        controllerName: CONTROLLER_NAME,
    });

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            registerController,
            { once: true }
        );
    } else {
        registerController();
    }
})();
