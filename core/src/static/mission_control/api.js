/* =============================================================================
   GENESIS VII-A0 — PACK 3B-1
   EXECUTIVE OPERATIONS CENTER API CLIENT
   ============================================================================= */

"use strict";

(() => {
    const CLIENT_VERSION = "Genesis VII-A0 Pack 3B-1";

    const DEFAULT_CONFIGURATION = Object.freeze({
        basePath: "/operations/executive",
        timeoutMilliseconds: 30000,
        retryAttempts: 2,
        retryBaseDelayMilliseconds: 400,
        retryMaximumDelayMilliseconds: 3000,
    });

    const ExecutiveApiEvents = Object.freeze({
        REQUEST_STARTED: "executive:api-request-started",
        REQUEST_SUCCEEDED: "executive:api-request-succeeded",
        REQUEST_FAILED: "executive:api-request-failed",
        REQUEST_RETRYING: "executive:api-request-retrying",
        CLIENT_READY: "executive:api-client-ready",
    });

    const ResourceNames = Object.freeze({
        DASHBOARD: "executive_dashboard",
        HEALTH: "executive_health",
        METRICS: "executive_metrics",
        STATUS: "executive_status",
        EVENTS: "executive_events",
        LIVE_STATUS: "executive_live_status",
    });

    const nowIso = () => new Date().toISOString();

    const sleep = (milliseconds) => (
        new Promise((resolve) => {
            window.setTimeout(resolve, milliseconds);
        })
    );

    const createRequestId = () => {
        if (
            window.crypto &&
            typeof window.crypto.randomUUID === "function"
        ) {
            return window.crypto.randomUUID();
        }

        return [
            "executive",
            Date.now().toString(36),
            Math.random().toString(36).slice(2),
        ].join("-");
    };

    const normalizeBasePath = (basePath) => {
        const value = String(basePath || "").trim();

        if (!value) {
            throw new Error("Executive API base path cannot be empty.");
        }

        return `/${value.replace(/^\/+|\/+$/g, "")}`;
    };

    const buildQueryString = (query = {}) => {
        const parameters = new URLSearchParams();

        for (const [key, value] of Object.entries(query)) {
            if (
                value === undefined ||
                value === null ||
                value === ""
            ) {
                continue;
            }

            if (Array.isArray(value)) {
                for (const item of value) {
                    parameters.append(key, String(item));
                }

                continue;
            }

            parameters.set(key, String(value));
        }

        const serialized = parameters.toString();

        return serialized ? `?${serialized}` : "";
    };

    class ExecutiveApiError extends Error {
        constructor(message, options = {}) {
            super(message);

            this.name = "ExecutiveApiError";
            this.requestId = options.requestId ?? null;
            this.endpoint = options.endpoint ?? null;
            this.method = options.method ?? null;
            this.status = options.status ?? null;
            this.statusText = options.statusText ?? null;
            this.payload = options.payload ?? null;
            this.retryable = Boolean(options.retryable);
            this.cause = options.cause;
            this.occurredAt = nowIso();
        }

        toJSON() {
            return {
                name: this.name,
                message: this.message,
                requestId: this.requestId,
                endpoint: this.endpoint,
                method: this.method,
                status: this.status,
                statusText: this.statusText,
                payload: this.payload,
                retryable: this.retryable,
                occurredAt: this.occurredAt,
            };
        }
    }

    class ExecutiveApiResponseError extends ExecutiveApiError {
        constructor(message, options = {}) {
            super(message, options);
            this.name = "ExecutiveApiResponseError";
        }
    }

    class ExecutiveApiTimeoutError extends ExecutiveApiError {
        constructor(message, options = {}) {
            super(message, options);
            this.name = "ExecutiveApiTimeoutError";
            this.retryable = true;
        }
    }

    class ExecutiveApiContractError extends ExecutiveApiError {
        constructor(message, options = {}) {
            super(message, options);
            this.name = "ExecutiveApiContractError";
            this.retryable = false;
        }
    }

    class ExecutiveApiClient {
        constructor(configuration = {}) {
            this.configuration = Object.freeze({
                ...DEFAULT_CONFIGURATION,
                ...configuration,
                basePath: normalizeBasePath(
                    configuration.basePath ??
                    DEFAULT_CONFIGURATION.basePath
                ),
            });

            this.requestSequence = 0;
            this.lastSuccessfulRequestAt = null;
            this.lastFailedRequestAt = null;
        }

        get basePath() {
            return this.configuration.basePath;
        }

        get version() {
            return CLIENT_VERSION;
        }

        emit(eventName, payload = {}) {
            if (
                window.JARVIS &&
                window.JARVIS.events &&
                typeof window.JARVIS.events.emit === "function"
            ) {
                window.JARVIS.events.emit(eventName, payload);
            }

            window.dispatchEvent(
                new CustomEvent(eventName, {
                    detail: {
                        emittedAt: nowIso(),
                        ...payload,
                    },
                })
            );
        }

        calculateRetryDelay(attempt) {
            const baseDelay =
                this.configuration.retryBaseDelayMilliseconds;

            const maximumDelay =
                this.configuration.retryMaximumDelayMilliseconds;

            const exponentialDelay = Math.min(
                maximumDelay,
                baseDelay * (2 ** Math.max(0, attempt - 1))
            );

            const jitter = Math.floor(
                Math.random() * Math.max(1, baseDelay / 2)
            );

            return Math.min(
                maximumDelay,
                exponentialDelay + jitter
            );
        }

        shouldRetry(error, attempt, maximumAttempts) {
            if (attempt >= maximumAttempts) {
                return false;
            }

            if (!(error instanceof ExecutiveApiError)) {
                return true;
            }

            return error.retryable;
        }

        async parseResponse(response, requestContext) {
            const contentType =
                response.headers.get("content-type") ?? "";

            let payload = null;

            if (contentType.includes("application/json")) {
                try {
                    payload = await response.json();
                } catch (error) {
                    throw new ExecutiveApiContractError(
                        "Executive API returned invalid JSON.",
                        {
                            ...requestContext,
                            status: response.status,
                            statusText: response.statusText,
                            cause: error,
                        }
                    );
                }
            } else {
                const text = await response.text();

                payload = text || null;
            }

            if (!response.ok) {
                const message =
                    payload &&
                    typeof payload === "object" &&
                    typeof payload.detail === "string"
                        ? payload.detail
                        : (
                            `Executive API request failed with ` +
                            `${response.status} ${response.statusText}.`
                        );

                throw new ExecutiveApiResponseError(
                    message,
                    {
                        ...requestContext,
                        status: response.status,
                        statusText: response.statusText,
                        payload,
                        retryable:
                            response.status === 408 ||
                            response.status === 425 ||
                            response.status === 429 ||
                            response.status >= 500,
                    }
                );
            }

            return payload;
        }

        validateTransportEnvelope(payload, expectedResource, context) {
            if (!payload || typeof payload !== "object") {
                throw new ExecutiveApiContractError(
                    "Executive API response is not an object.",
                    {
                        ...context,
                        payload,
                    }
                );
            }

            if (payload.ok !== true) {
                throw new ExecutiveApiContractError(
                    "Executive API response did not declare success.",
                    {
                        ...context,
                        payload,
                    }
                );
            }

            if (
                expectedResource &&
                payload.resource !== expectedResource
            ) {
                throw new ExecutiveApiContractError(
                    (
                        `Executive API returned resource ` +
                        `'${payload.resource}' instead of ` +
                        `'${expectedResource}'.`
                    ),
                    {
                        ...context,
                        payload,
                    }
                );
            }

            if (
                !Object.prototype.hasOwnProperty.call(
                    payload,
                    "data"
                )
            ) {
                throw new ExecutiveApiContractError(
                    "Executive API response does not contain data.",
                    {
                        ...context,
                        payload,
                    }
                );
            }

            return payload;
        }

        async request(path, options = {}) {
            const method = String(
                options.method ?? "GET"
            ).toUpperCase();

            const query = options.query ?? {};
            const expectedResource =
                options.expectedResource ?? null;

            const timeoutMilliseconds =
                options.timeoutMilliseconds ??
                this.configuration.timeoutMilliseconds;

            const retryAttempts =
                options.retryAttempts ??
                this.configuration.retryAttempts;

            const maximumAttempts = Math.max(
                1,
                retryAttempts + 1
            );

            const endpoint =
                `${this.basePath}/${String(path).replace(/^\/+/, "")}` +
                buildQueryString(query);

            const requestId = createRequestId();

            const requestContext = {
                requestId,
                endpoint,
                method,
            };

            this.requestSequence += 1;

            let finalError = null;

            for (
                let attempt = 1;
                attempt <= maximumAttempts;
                attempt += 1
            ) {
                const controller = new AbortController();

                const timeoutId = window.setTimeout(
                    () => controller.abort(),
                    timeoutMilliseconds
                );

                this.emit(
                    ExecutiveApiEvents.REQUEST_STARTED,
                    {
                        ...requestContext,
                        attempt,
                        maximumAttempts,
                    }
                );

                try {
                    const headers = new Headers(
                        options.headers ?? {}
                    );

                    headers.set(
                        "Accept",
                        "application/json"
                    );

                    headers.set(
                        "X-JARVIS-Request-ID",
                        requestId
                    );

                    const fetchOptions = {
                        method,
                        headers,
                        signal: controller.signal,
                        credentials:
                            options.credentials ?? "same-origin",
                        cache: options.cache ?? "no-store",
                    };

                    if (options.body !== undefined) {
                        if (
                            typeof options.body === "string" ||
                            options.body instanceof FormData ||
                            options.body instanceof Blob
                        ) {
                            fetchOptions.body = options.body;
                        } else {
                            headers.set(
                                "Content-Type",
                                "application/json"
                            );

                            fetchOptions.body = JSON.stringify(
                                options.body
                            );
                        }
                    }

                    const response = await window.fetch(
                        endpoint,
                        fetchOptions
                    );

                    const payload = await this.parseResponse(
                        response,
                        requestContext
                    );

                    const envelope =
                        this.validateTransportEnvelope(
                            payload,
                            expectedResource,
                            requestContext
                        );

                    this.lastSuccessfulRequestAt = nowIso();

                    this.emit(
                        ExecutiveApiEvents.REQUEST_SUCCEEDED,
                        {
                            ...requestContext,
                            attempt,
                            status: response.status,
                            resource: envelope.resource,
                        }
                    );

                    return envelope;
                } catch (error) {
                    let normalizedError;

                    if (
                        error &&
                        error.name === "AbortError"
                    ) {
                        normalizedError =
                            new ExecutiveApiTimeoutError(
                                (
                                    `Executive API request exceeded ` +
                                    `${timeoutMilliseconds} ms.`
                                ),
                                {
                                    ...requestContext,
                                    cause: error,
                                }
                            );
                    } else if (
                        error instanceof ExecutiveApiError
                    ) {
                        normalizedError = error;
                    } else {
                        normalizedError =
                            new ExecutiveApiError(
                                (
                                    error instanceof Error
                                        ? error.message
                                        : String(error)
                                ),
                                {
                                    ...requestContext,
                                    cause: error,
                                    retryable: true,
                                }
                            );
                    }

                    finalError = normalizedError;
                    this.lastFailedRequestAt = nowIso();

                    const retry =
                        method === "GET" &&
                        this.shouldRetry(
                            normalizedError,
                            attempt,
                            maximumAttempts
                        );

                    if (!retry) {
                        this.emit(
                            ExecutiveApiEvents.REQUEST_FAILED,
                            {
                                ...requestContext,
                                attempt,
                                error:
                                    normalizedError.toJSON(),
                            }
                        );

                        throw normalizedError;
                    }

                    const delayMilliseconds =
                        this.calculateRetryDelay(attempt);

                    this.emit(
                        ExecutiveApiEvents.REQUEST_RETRYING,
                        {
                            ...requestContext,
                            attempt,
                            nextAttempt: attempt + 1,
                            delayMilliseconds,
                            error: normalizedError.toJSON(),
                        }
                    );

                    await sleep(delayMilliseconds);
                } finally {
                    window.clearTimeout(timeoutId);
                }
            }

            throw finalError ?? new ExecutiveApiError(
                "Executive API request failed.",
                requestContext
            );
        }

        async dashboard(options = {}) {
            return this.request(
                "dashboard",
                {
                    query: {
                        refresh: Boolean(options.refresh),
                    },
                    expectedResource: ResourceNames.DASHBOARD,
                    ...options,
                }
            );
        }

        async health(options = {}) {
            return this.request(
                "health",
                {
                    query: {
                        refresh: Boolean(options.refresh),
                    },
                    expectedResource: ResourceNames.HEALTH,
                    ...options,
                }
            );
        }

        async metrics(options = {}) {
            return this.request(
                "metrics",
                {
                    query: {
                        refresh: Boolean(options.refresh),
                    },
                    expectedResource: ResourceNames.METRICS,
                    ...options,
                }
            );
        }

        async status(options = {}) {
            return this.request(
                "status",
                {
                    query: {
                        refresh: Boolean(options.refresh),
                    },
                    expectedResource: ResourceNames.STATUS,
                    ...options,
                }
            );
        }

        async events(options = {}) {
            return this.request(
                "events",
                {
                    expectedResource: ResourceNames.EVENTS,
                    ...options,
                }
            );
        }

        async liveStatus(options = {}) {
            return this.request(
                "live/status",
                {
                    expectedResource: ResourceNames.LIVE_STATUS,
                    ...options,
                }
            );
        }

        diagnostics() {
            return Object.freeze({
                version: this.version,
                basePath: this.basePath,
                requestSequence: this.requestSequence,
                lastSuccessfulRequestAt:
                    this.lastSuccessfulRequestAt,
                lastFailedRequestAt:
                    this.lastFailedRequestAt,
                timeoutMilliseconds:
                    this.configuration.timeoutMilliseconds,
                retryAttempts:
                    this.configuration.retryAttempts,
            });
        }
    }

    class ExecutiveApiController {
        constructor(client) {
            this.client = client;
            this.application = null;
            this.unsubscribers = [];
        }

        async initialize(application) {
            this.application = application;

            application.state.set(
                "runtime.api",
                {
                    state: "ready",
                    version: this.client.version,
                    basePath: this.client.basePath,
                    initializedAt: nowIso(),
                },
                {
                    source: "executive-api-controller",
                }
            );

            this.unsubscribers.push(
                application.events.on(
                    ExecutiveApiEvents.REQUEST_STARTED,
                    () => {
                        application.setLoading(true);
                    }
                )
            );

            this.unsubscribers.push(
                application.events.on(
                    ExecutiveApiEvents.REQUEST_SUCCEEDED,
                    ({ emittedAt }) => {
                        application.setLoading(false);

                        application.state.set(
                            "connection.lastMessageAt",
                            emittedAt,
                            {
                                source:
                                    "executive-api-controller",
                            }
                        );
                    }
                )
            );

            this.unsubscribers.push(
                application.events.on(
                    ExecutiveApiEvents.REQUEST_FAILED,
                    ({ error }) => {
                        application.setLoading(false);

                        application.reportError(
                            new ExecutiveApiError(
                                error.message,
                                error
                            ),
                            {
                                source:
                                    "executive-api-client",
                                fatal: false,
                            }
                        );
                    }
                )
            );

            application.events.emit(
                ExecutiveApiEvents.CLIENT_READY,
                {
                    version: this.client.version,
                    basePath: this.client.basePath,
                }
            );
        }

        stop() {
            for (const unsubscribe of this.unsubscribers) {
                unsubscribe();
            }

            this.unsubscribers = [];
        }
    }

    const apiClient = new ExecutiveApiClient();

    window.JARVIS_API = Object.freeze({
        client: apiClient,

        events: ExecutiveApiEvents,
        resources: ResourceNames,

        errors: Object.freeze({
            ExecutiveApiError,
            ExecutiveApiResponseError,
            ExecutiveApiTimeoutError,
            ExecutiveApiContractError,
        }),

        dashboard(options = {}) {
            return apiClient.dashboard(options);
        },

        health(options = {}) {
            return apiClient.health(options);
        },

        metrics(options = {}) {
            return apiClient.metrics(options);
        },

        status(options = {}) {
            return apiClient.status(options);
        },

        eventsEndpoint(options = {}) {
            return apiClient.events(options);
        },

        liveStatus(options = {}) {
            return apiClient.liveStatus(options);
        },

        request(path, options = {}) {
            return apiClient.request(path, options);
        },

        diagnostics() {
            return apiClient.diagnostics();
        },

        version: CLIENT_VERSION,
    });

    const registerController = () => {
        if (
            !window.JARVIS ||
            typeof window.JARVIS.registerController !== "function"
        ) {
            console.warn(
                "[Executive API] JARVIS runtime unavailable; " +
                "API controller registration skipped."
            );

            return;
        }

        try {
            window.JARVIS.registerController(
                "api",
                new ExecutiveApiController(apiClient)
            );

            const lifecycle =
                window.JARVIS.state.get(
                    "application.lifecycle",
                    "created"
                );

            if (
                lifecycle === "ready" &&
                window.JARVIS.controllers &&
                typeof window.JARVIS.controllers.initializeAll ===
                    "function"
            ) {
                void window.JARVIS.controllers.initializeAll();
            }
        } catch (error) {
            window.JARVIS.reportError(
                error,
                {
                    source: "executive-api-registration",
                    fatal: false,
                }
            );
        }
    };

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
