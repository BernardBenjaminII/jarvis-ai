/* =============================================================================
   GENESIS VII-A0 — PACK 3A-3.1
   EXECUTIVE OPERATIONS CENTER APPLICATION RUNTIME
   ============================================================================= */

"use strict";

(() => {
    const APPLICATION_NAME = "JARVIS Executive Operations Center";
    const APPLICATION_VERSION = "Genesis VII-A0 Pack 3A-3.1";
    const STORAGE_NAMESPACE = "jarvis.executive_operations";
    const DEFAULT_VIEW = "knowledge";

    const ApplicationLifecycle = Object.freeze({
        CREATED: "created",
        INITIALIZING: "initializing",
        READY: "ready",
        DEGRADED: "degraded",
        FAILED: "failed",
        STOPPED: "stopped",
    });

    const ConnectionState = Object.freeze({
        INITIALIZING: "initializing",
        CONNECTING: "connecting",
        CONNECTED: "connected",
        DEGRADED: "degraded",
        DISCONNECTED: "disconnected",
        UNKNOWN: "unknown",
    });

    const HealthState = Object.freeze({
        HEALTHY: "healthy",
        DEGRADED: "degraded",
        CRITICAL: "critical",
        UNAVAILABLE: "unavailable",
        UNKNOWN: "unknown",
    });

    const RuntimeEvents = Object.freeze({
        APPLICATION_INITIALIZING: "executive:application-initializing",
        APPLICATION_READY: "executive:application-ready",
        APPLICATION_DEGRADED: "executive:application-degraded",
        APPLICATION_FAILED: "executive:application-failed",
        APPLICATION_STOPPED: "executive:application-stopped",

        STATE_CHANGED: "executive:state-changed",
        CONNECTION_CHANGED: "executive:connection-changed",
        HEALTH_CHANGED: "executive:health-changed",
        VIEW_REQUESTED: "executive:view-requested",
        REFRESH_REQUESTED: "executive:refresh-requested",
        ERROR_REPORTED: "executive:error-reported",
        NOTIFICATION_CREATED: "executive:notification-created",
        CLOCK_TICK: "executive:clock-tick",
    });

    const nowIso = () => new Date().toISOString();

    const freezeCopy = (value) => {
        if (Array.isArray(value)) {
            return Object.freeze(value.map(freezeCopy));
        }

        if (value && typeof value === "object") {
            const copy = {};

            for (const [key, child] of Object.entries(value)) {
                copy[key] = freezeCopy(child);
            }

            return Object.freeze(copy);
        }

        return value;
    };

    class ExecutiveEventBus {
        constructor() {
            this.listeners = new Map();
        }

        on(eventName, listener) {
            if (typeof listener !== "function") {
                throw new TypeError("Event listener must be a function.");
            }

            const listeners = this.listeners.get(eventName) ?? new Set();
            listeners.add(listener);
            this.listeners.set(eventName, listeners);

            return () => this.off(eventName, listener);
        }

        once(eventName, listener) {
            const unsubscribe = this.on(eventName, (payload) => {
                unsubscribe();
                listener(payload);
            });

            return unsubscribe;
        }

        off(eventName, listener) {
            const listeners = this.listeners.get(eventName);

            if (!listeners) {
                return;
            }

            listeners.delete(listener);

            if (listeners.size === 0) {
                this.listeners.delete(eventName);
            }
        }

        emit(eventName, payload = {}) {
            const listeners = this.listeners.get(eventName);

            if (!listeners || listeners.size === 0) {
                return;
            }

            const eventPayload = freezeCopy({
                eventName,
                emittedAt: nowIso(),
                ...payload,
            });

            for (const listener of [...listeners]) {
                try {
                    listener(eventPayload);
                } catch (error) {
                    console.error(
                        `[ExecutiveEventBus] Listener failed for ${eventName}`,
                        error
                    );
                }
            }
        }

        clear() {
            this.listeners.clear();
        }
    }

    class ExecutiveStorage {
        constructor(namespace) {
            this.namespace = namespace;
            this.available = this.detectAvailability();
        }

        detectAvailability() {
            try {
                const probe = `${this.namespace}.probe`;
                window.localStorage.setItem(probe, "1");
                window.localStorage.removeItem(probe);
                return true;
            } catch {
                return false;
            }
        }

        key(name) {
            return `${this.namespace}.${name}`;
        }

        get(name, fallback = null) {
            if (!this.available) {
                return fallback;
            }

            try {
                const rawValue = window.localStorage.getItem(this.key(name));

                if (rawValue === null) {
                    return fallback;
                }

                return JSON.parse(rawValue);
            } catch (error) {
                console.warn(
                    `[ExecutiveStorage] Unable to read ${name}`,
                    error
                );
                return fallback;
            }
        }

        set(name, value) {
            if (!this.available) {
                return false;
            }

            try {
                window.localStorage.setItem(
                    this.key(name),
                    JSON.stringify(value)
                );
                return true;
            } catch (error) {
                console.warn(
                    `[ExecutiveStorage] Unable to write ${name}`,
                    error
                );
                return false;
            }
        }

        remove(name) {
            if (!this.available) {
                return false;
            }

            try {
                window.localStorage.removeItem(this.key(name));
                return true;
            } catch {
                return false;
            }
        }
    }

    class ExecutiveStateStore {
        constructor(eventBus) {
            this.eventBus = eventBus;
            this.state = {
                application: {
                    name: APPLICATION_NAME,
                    version: APPLICATION_VERSION,
                    lifecycle: ApplicationLifecycle.CREATED,
                    initializedAt: null,
                    readyAt: null,
                },

                navigation: {
                    activeView: DEFAULT_VIEW,
                    previousView: null,
                    sidebarState: "expanded",
                    mobileNavigationOpen: false,
                },

                connection: {
                    state: ConnectionState.INITIALIZING,
                    lastConnectedAt: null,
                    lastDisconnectedAt: null,
                    lastMessageAt: null,
                },

                dashboard: {
                    loading: false,
                    lastRefreshRequestedAt: null,
                    lastUpdatedAt: null,
                },

                health: {
                    state: HealthState.UNKNOWN,
                    checks: [],
                },

                metrics: {
                    values: {},
                    available: 0,
                    unavailable: 0,
                    notConfigured: 0,
                },

                notifications: [],

                runtime: {
                    clock: null,
                    controllers: {},
                    errors: [],
                },
            };
        }

        snapshot() {
            return freezeCopy(structuredClone(this.state));
        }

        get(path, fallback = undefined) {
            if (!path) {
                return this.snapshot();
            }

            const segments = path.split(".");
            let current = this.state;

            for (const segment of segments) {
                if (
                    current === null ||
                    typeof current !== "object" ||
                    !(segment in current)
                ) {
                    return fallback;
                }

                current = current[segment];
            }

            return freezeCopy(structuredClone(current));
        }

        set(path, value, metadata = {}) {
            const segments = path.split(".");
            const finalKey = segments.pop();

            if (!finalKey) {
                throw new Error("State path cannot be empty.");
            }

            let target = this.state;

            for (const segment of segments) {
                if (
                    !Object.prototype.hasOwnProperty.call(target, segment) ||
                    target[segment] === null ||
                    typeof target[segment] !== "object"
                ) {
                    target[segment] = {};
                }

                target = target[segment];
            }

            const previousValue = target[finalKey];
            target[finalKey] = value;

            this.eventBus.emit(RuntimeEvents.STATE_CHANGED, {
                path,
                previousValue,
                value,
                metadata,
            });
        }

        update(path, updater, metadata = {}) {
            if (typeof updater !== "function") {
                throw new TypeError("State updater must be a function.");
            }

            const currentValue = this.get(path);
            const nextValue = updater(currentValue);
            this.set(path, nextValue, metadata);
        }
    }

    class ExecutiveDomRegistry {
        constructor() {
            this.elements = new Map();
        }

        register(name, selector, options = {}) {
            const {
                required = false,
                all = false,
                root = document,
            } = options;

            const value = all
                ? [...root.querySelectorAll(selector)]
                : root.querySelector(selector);

            const missing = all ? value.length === 0 : value === null;

            if (required && missing) {
                throw new Error(
                    `Required DOM element '${name}' not found: ${selector}`
                );
            }

            this.elements.set(name, value);
            return value;
        }

        get(name) {
            return this.elements.get(name) ?? null;
        }

        require(name) {
            const value = this.get(name);

            if (value === null) {
                throw new Error(`DOM reference '${name}' is unavailable.`);
            }

            return value;
        }

        has(name) {
            return this.elements.has(name) && this.get(name) !== null;
        }

        clear() {
            this.elements.clear();
        }
    }

    class ExecutiveControllerRegistry {
        constructor(application) {
            this.application = application;
            this.controllers = new Map();
            this.initialized = new Set();
        }

        register(name, controller) {
            if (!name || typeof name !== "string") {
                throw new TypeError("Controller name must be a string.");
            }

            if (!controller || typeof controller !== "object") {
                throw new TypeError(
                    `Controller '${name}' must be an object.`
                );
            }

            if (this.controllers.has(name)) {
                throw new Error(
                    `Controller '${name}' is already registered.`
                );
            }

            this.controllers.set(name, controller);
            return controller;
        }

        get(name) {
            return this.controllers.get(name) ?? null;
        }

        async initializeAll() {
            for (const [name, controller] of this.controllers.entries()) {
                if (this.initialized.has(name)) {
                    continue;
                }

                if (typeof controller.initialize === "function") {
                    await controller.initialize(this.application);
                }

                this.initialized.add(name);

                this.application.state.set(
                    `runtime.controllers.${name}`,
                    {
                        state: "ready",
                        initializedAt: nowIso(),
                    },
                    { source: "controller-registry" }
                );
            }
        }

        async initialize(name) {
            const controller = this.controllers.get(name);
            if (!controller || this.initialized.has(name)) {
                return controller ?? null;
            }
            if (typeof controller.initialize === "function") {
                await controller.initialize(this.application);
            }
            this.initialized.add(name);
            this.application.state.set(
                `runtime.controllers.${name}`,
                { state: "ready", initializedAt: nowIso() },
                { source: "controller-registry" }
            );
            return controller;
        }

        async stopAll() {
            const entries = [...this.controllers.entries()].reverse();

            for (const [name, controller] of entries) {
                try {
                    if (typeof controller.stop === "function") {
                        await controller.stop(this.application);
                    }
                } catch (error) {
                    console.error(
                        `[ExecutiveControllerRegistry] Stop failed: ${name}`,
                        error
                    );
                }
            }

            this.initialized.clear();
        }
    }

    class ExecutiveClockController {
        constructor() {
            this.intervalId = null;
        }

        initialize(application) {
            this.application = application;
            this.tick();

            this.intervalId = window.setInterval(
                () => this.tick(),
                1000
            );
        }

        tick() {
            const now = new Date();
            const clockValue = now.toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
                hour12: false,
            });

            const clockElement = this.application.dom.get(
                "sidebarExecutiveClock"
            );

            if (clockElement) {
                clockElement.textContent = clockValue;
                clockElement.dateTime = now.toISOString();
            }

            this.application.state.set(
                "runtime.clock",
                now.toISOString(),
                { source: "executive-clock" }
            );

            this.application.events.emit(RuntimeEvents.CLOCK_TICK, {
                timestamp: now.toISOString(),
                displayValue: clockValue,
            });
        }

        stop() {
            if (this.intervalId !== null) {
                window.clearInterval(this.intervalId);
                this.intervalId = null;
            }
        }
    }

    class ExecutiveConnectionProjectionController {
        initialize(application) {
            this.application = application;

            this.unsubscribe = application.events.on(
                RuntimeEvents.CONNECTION_CHANGED,
                ({ state }) => this.render(state)
            );

            this.render(
                application.state.get(
                    "connection.state",
                    ConnectionState.UNKNOWN
                )
            );
        }

        render(state) {
            const normalizedState = Object.values(ConnectionState).includes(state)
                ? state
                : ConnectionState.UNKNOWN;

            const labels = {
                [ConnectionState.INITIALIZING]: "Initializing",
                [ConnectionState.CONNECTING]: "Connecting",
                [ConnectionState.CONNECTED]: "Connected",
                [ConnectionState.DEGRADED]: "Degraded",
                [ConnectionState.DISCONNECTED]: "Disconnected",
                [ConnectionState.UNKNOWN]: "Unknown",
            };

            const applicationRoot = this.application.dom.get(
                "applicationRoot"
            );

            if (applicationRoot) {
                applicationRoot.dataset.connectionState = normalizedState;
            }

            const indicatorNames = [
                "sidebarConnectionIndicator",
                "commandBarConnectionIndicator",
                "statusBarConnectionIndicator",
            ];

            for (const name of indicatorNames) {
                const indicator = this.application.dom.get(name);

                if (!indicator) {
                    continue;
                }

                indicator.className =
                    `status-indicator status-indicator--${normalizedState}`;
            }

            const label = labels[normalizedState];

            const sidebarLabel = this.application.dom.get(
                "sidebarConnectionState"
            );

            const commandBarLabel = this.application.dom.get(
                "commandBarConnectionLabel"
            );

            const statusBarLabel = this.application.dom.get(
                "statusBarConnection"
            );

            if (sidebarLabel) {
                sidebarLabel.textContent = label;
            }

            if (commandBarLabel) {
                commandBarLabel.textContent = label;
            }

            if (statusBarLabel) {
                statusBarLabel.textContent = `Executive link ${label.toLowerCase()}`;
            }
        }

        stop() {
            this.unsubscribe?.();
        }
    }

    class ExecutiveRefreshController {
        initialize(application) {
            this.application = application;
            this.refreshButton = application.dom.get(
                "refreshDashboardButton"
            );
            this.retryButton = application.dom.get(
                "errorRetryButton"
            );

            this.handleRefresh = () => this.requestRefresh("manual");

            this.refreshButton?.addEventListener(
                "click",
                this.handleRefresh
            );

            this.retryButton?.addEventListener(
                "click",
                this.handleRefresh
            );
        }

        requestRefresh(source) {
            const requestedAt = nowIso();

            this.application.state.set(
                "dashboard.lastRefreshRequestedAt",
                requestedAt,
                { source }
            );

            this.application.events.emit(
                RuntimeEvents.REFRESH_REQUESTED,
                {
                    source,
                    requestedAt,
                }
            );
        }

        stop() {
            this.refreshButton?.removeEventListener(
                "click",
                this.handleRefresh
            );

            this.retryButton?.removeEventListener(
                "click",
                this.handleRefresh
            );
        }
    }

    class ExecutiveErrorController {
        initialize(application) {
            this.application = application;

            this.unsubscribe = application.events.on(
                RuntimeEvents.ERROR_REPORTED,
                (payload) => this.present(payload)
            );
        }

        present(payload) {
            const {
                message = "An unexpected Executive runtime error occurred.",
                details = "",
                fatal = false,
            } = payload;

            const messageElement = this.application.dom.get(
                "errorMessage"
            );
            const detailsElement = this.application.dom.get(
                "errorDetails"
            );
            const dialog = this.application.dom.get("errorDialog");

            if (messageElement) {
                messageElement.textContent = message;
            }

            if (detailsElement) {
                detailsElement.textContent = details;
                detailsElement.hidden = !details;
            }

            if (
                dialog &&
                typeof dialog.showModal === "function" &&
                !dialog.open
            ) {
                dialog.showModal();
            }

            if (fatal) {
                this.application.setLifecycle(
                    ApplicationLifecycle.FAILED
                );
            }
        }

        stop() {
            this.unsubscribe?.();
        }
    }

    class ExecutiveApplication {
        constructor() {
            this.events = new ExecutiveEventBus();
            this.storage = new ExecutiveStorage(STORAGE_NAMESPACE);
            this.state = new ExecutiveStateStore(this.events);
            this.dom = new ExecutiveDomRegistry();
            this.controllers = new ExecutiveControllerRegistry(this);
            this.started = false;
            this.stopping = false;
        }

        cacheDom() {
            this.dom.register(
                "applicationRoot",
                "#executive-application",
                { required: true }
            );

            this.dom.register(
                "executiveMain",
                "#executive-main",
                { required: true }
            );

            this.dom.register(
                "sidebar",
                "#executive-sidebar",
                { required: true }
            );

            this.dom.register(
                "navigationItems",
                "[data-view]",
                { all: true }
            );

            this.dom.register(
                "viewPanels",
                "[data-view-panel]",
                { all: true }
            );

            this.dom.register(
                "openViewButtons",
                "[data-open-view]",
                { all: true }
            );

            this.dom.register(
                "sidebarExecutiveClock",
                "#sidebar-executive-clock"
            );

            this.dom.register(
                "sidebarConnectionIndicator",
                "#sidebar-connection-indicator"
            );

            this.dom.register(
                "sidebarConnectionState",
                "#sidebar-connection-state"
            );

            this.dom.register(
                "commandBarConnectionIndicator",
                "#command-bar-connection-indicator"
            );

            this.dom.register(
                "commandBarConnectionLabel",
                "#command-bar-connection-label"
            );

            this.dom.register(
                "statusBarConnectionIndicator",
                "#status-bar-connection-indicator"
            );

            this.dom.register(
                "statusBarConnection",
                "#status-bar-connection"
            );

            this.dom.register(
                "refreshDashboardButton",
                "#refresh-dashboard-button"
            );

            this.dom.register(
                "errorDialog",
                "#executive-error-dialog"
            );

            this.dom.register(
                "errorMessage",
                "#executive-error-message"
            );

            this.dom.register(
                "errorDetails",
                "#executive-error-details"
            );

            this.dom.register(
                "errorRetryButton",
                "#executive-error-retry"
            );

            this.dom.register(
                "globalAnnouncer",
                "#global-announcer"
            );

            this.dom.register(
                "statusBarLastUpdate",
                "#status-bar-last-update"
            );
        }

        registerCoreControllers() {
            this.controllers.register(
                "clock",
                new ExecutiveClockController()
            );

            this.controllers.register(
                "connectionProjection",
                new ExecutiveConnectionProjectionController()
            );

            this.controllers.register(
                "refresh",
                new ExecutiveRefreshController()
            );

            this.controllers.register(
                "errors",
                new ExecutiveErrorController()
            );
        }

        setLifecycle(lifecycle) {
            if (!Object.values(ApplicationLifecycle).includes(lifecycle)) {
                throw new Error(
                    `Invalid application lifecycle: ${lifecycle}`
                );
            }

            this.state.set(
                "application.lifecycle",
                lifecycle,
                { source: "application-runtime" }
            );

            const applicationRoot = this.dom.get("applicationRoot");

            if (applicationRoot) {
                applicationRoot.dataset.applicationState = lifecycle;
            }
        }

        setConnectionState(state, metadata = {}) {
            if (!Object.values(ConnectionState).includes(state)) {
                state = ConnectionState.UNKNOWN;
            }

            const previousState = this.state.get("connection.state");

            this.state.set(
                "connection.state",
                state,
                {
                    source: metadata.source ?? "runtime",
                    ...metadata,
                }
            );

            if (state === ConnectionState.CONNECTED) {
                this.state.set(
                    "connection.lastConnectedAt",
                    nowIso(),
                    { source: "runtime" }
                );
            }

            if (state === ConnectionState.DISCONNECTED) {
                this.state.set(
                    "connection.lastDisconnectedAt",
                    nowIso(),
                    { source: "runtime" }
                );
            }

            this.events.emit(RuntimeEvents.CONNECTION_CHANGED, {
                state,
                previousState,
                metadata,
            });
        }

        setHealthState(state, metadata = {}) {
            if (!Object.values(HealthState).includes(state)) {
                state = HealthState.UNKNOWN;
            }

            const previousState = this.state.get("health.state");

            this.state.set(
                "health.state",
                state,
                {
                    source: metadata.source ?? "runtime",
                    ...metadata,
                }
            );

            this.events.emit(RuntimeEvents.HEALTH_CHANGED, {
                state,
                previousState,
                metadata,
            });
        }

        setLoading(loading) {
            const normalized = Boolean(loading);

            this.state.set(
                "dashboard.loading",
                normalized,
                { source: "application-runtime" }
            );

            const main = this.dom.get("executiveMain");
            const refreshButton = this.dom.get(
                "refreshDashboardButton"
            );

            if (main) {
                main.dataset.loading = String(normalized);
                main.setAttribute(
                    "aria-busy",
                    String(normalized)
                );
            }

            if (refreshButton) {
                refreshButton.disabled = normalized;
            }
        }

        announce(message) {
            const announcer = this.dom.get("globalAnnouncer");

            if (!announcer) {
                return;
            }

            announcer.textContent = "";

            window.requestAnimationFrame(() => {
                announcer.textContent = message;
            });
        }

        reportError(error, context = {}) {
            const normalizedError =
                error instanceof Error
                    ? error
                    : new Error(String(error));

            const record = {
                message: normalizedError.message,
                name: normalizedError.name,
                stack: normalizedError.stack ?? "",
                context,
                reportedAt: nowIso(),
            };

            this.state.update(
                "runtime.errors",
                (errors = []) => [...errors, record].slice(-50),
                { source: "error-handler" }
            );

            console.error(
                "[ExecutiveApplication]",
                normalizedError,
                context
            );

            this.events.emit(RuntimeEvents.ERROR_REPORTED, {
                message: normalizedError.message,
                details: normalizedError.stack ?? "",
                fatal: Boolean(context.fatal),
                context,
            });
        }

        installGlobalErrorHandlers() {
            window.addEventListener("error", (event) => {
                this.reportError(
                    event.error ?? new Error(event.message),
                    {
                        source: "window.error",
                        filename: event.filename,
                        line: event.lineno,
                        column: event.colno,
                        fatal: false,
                    }
                );
            });

            window.addEventListener(
                "unhandledrejection",
                (event) => {
                    this.reportError(
                        event.reason ?? new Error(
                            "Unhandled promise rejection"
                        ),
                        {
                            source: "window.unhandledrejection",
                            fatal: false,
                        }
                    );
                }
            );
        }

        installLifecycleHandlers() {
            window.addEventListener(
                "pagehide",
                () => {
                    void this.stop();
                },
                { once: true }
            );

            document.addEventListener(
                "visibilitychange",
                () => {
                    if (document.visibilityState === "visible") {
                        this.events.emit(
                            RuntimeEvents.REFRESH_REQUESTED,
                            {
                                source: "document-visible",
                                requestedAt: nowIso(),
                            }
                        );
                    }
                }
            );
        }

        async start() {
            if (this.started) {
                return;
            }

            this.started = true;
            this.setLifecycle(ApplicationLifecycle.INITIALIZING);

            this.state.set(
                "application.initializedAt",
                nowIso(),
                { source: "application-runtime" }
            );

            this.events.emit(
                RuntimeEvents.APPLICATION_INITIALIZING,
                {
                    applicationName: APPLICATION_NAME,
                    version: APPLICATION_VERSION,
                }
            );

            try {
                this.cacheDom();
                this.installGlobalErrorHandlers();
                this.installLifecycleHandlers();
                this.registerCoreControllers();

                await this.controllers.initializeAll();

                this.setConnectionState(
                    ConnectionState.DISCONNECTED,
                    {
                        source: "bootstrap",
                        reason: "Live transport not connected in Pack 3A-3.1",
                    }
                );

                this.setLifecycle(ApplicationLifecycle.READY);

                const readyAt = nowIso();

                this.state.set(
                    "application.readyAt",
                    readyAt,
                    { source: "application-runtime" }
                );

                this.events.emit(
                    RuntimeEvents.APPLICATION_READY,
                    {
                        readyAt,
                        applicationName: APPLICATION_NAME,
                        version: APPLICATION_VERSION,
                    }
                );

                this.announce(
                    "Executive Operations Center initialized."
                );

                console.info(
                    `[${APPLICATION_NAME}] ${APPLICATION_VERSION} ready`
                );
            } catch (error) {
                this.setLifecycle(ApplicationLifecycle.FAILED);

                this.reportError(error, {
                    source: "application-startup",
                    fatal: true,
                });

                this.events.emit(
                    RuntimeEvents.APPLICATION_FAILED,
                    {
                        message:
                            error instanceof Error
                                ? error.message
                                : String(error),
                    }
                );

                throw error;
            }
        }

        async stop() {
            if (!this.started || this.stopping) {
                return;
            }

            this.stopping = true;

            try {
                await this.controllers.stopAll();
                this.setLifecycle(ApplicationLifecycle.STOPPED);

                this.events.emit(
                    RuntimeEvents.APPLICATION_STOPPED,
                    {
                        stoppedAt: nowIso(),
                    }
                );
            } finally {
                this.stopping = false;
                this.started = false;
            }
        }
    }

    const application = new ExecutiveApplication();

    window.JARVIS = Object.freeze({
        application,
        events: application.events,
        state: application.state,
        dom: application.dom,
        controllers: application.controllers,
        storage: application.storage,

        lifecycle: ApplicationLifecycle,
        connectionStates: ConnectionState,
        healthStates: HealthState,
        runtimeEvents: RuntimeEvents,

        version: APPLICATION_VERSION,

        registerController(name, controller) {
            return application.controllers.register(
                name,
                controller
            );
        },

        requestRefresh(source = "external") {
            application.events.emit(
                RuntimeEvents.REFRESH_REQUESTED,
                {
                    source,
                    requestedAt: nowIso(),
                }
            );
        },

        setConnectionState(state, metadata = {}) {
            application.setConnectionState(state, metadata);
        },

        setHealthState(state, metadata = {}) {
            application.setHealthState(state, metadata);
        },

        setLoading(loading) {
            application.setLoading(loading);
        },

        reportError(error, context = {}) {
            application.reportError(error, context);
        },

        snapshot() {
            return application.state.snapshot();
        },
    });

    const bootstrap = async () => {
        try {
            await application.start();
        } catch (error) {
            console.error(
                "[Executive Bootstrap] Application failed to start.",
                error
            );
        }
    };

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            bootstrap,
            { once: true }
        );
    } else {
        void bootstrap();
    }
})();
