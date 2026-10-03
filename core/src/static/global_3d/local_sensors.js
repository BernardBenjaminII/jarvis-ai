(() => {
    "use strict";

    const STATUS_URL = "/api/sensors/status";

    /*
     * This endpoint performs a real RTL-SDR hardware probe.
     * Keep the interval conservative so Global 3D does not
     * continuously detach/re-attach the receiver's kernel driver.
     */
    const REFRESH_MS = 30000;

    let timer = null;

    function el(id) {
        return document.getElementById(id);
    }

    function setText(id, value) {
        const node = el(id);

        if (node) {
            node.textContent = value;
        }
    }

    function stateLabel(value) {
        return String(value || "unknown")
            .replaceAll("_", " ")
            .toUpperCase();
    }

    function setIndicator(id, state) {
        const node = el(id);

        if (!node) {
            return;
        }

        node.classList.remove(
            "ready",
            "warning",
            "offline"
        );

        if (state === "ready" || state === "fix") {
            node.classList.add("ready");
            return;
        }

        if (
            state === "no_fix" ||
            state === "busy" ||
            state === "permission_denied"
        ) {
            node.classList.add("warning");
            return;
        }

        node.classList.add("offline");
    }

    function formatRate(rate) {
        const value = Number(rate);

        if (!Number.isFinite(value)) {
            return null;
        }

        if (value >= 1000000) {
            return `${(value / 1000000).toFixed(3)} MS/s`;
        }

        if (value >= 1000) {
            return `${(value / 1000).toFixed(1)} kS/s`;
        }

        return `${value} S/s`;
    }

    function renderSdr(sdr) {
        const state = sdr?.state || "unavailable";

        setText(
            "localSdrState",
            stateLabel(state)
        );

        setIndicator(
            "localSdrIndicator",
            state
        );

        const pieces = [];

        if (sdr?.product) {
            pieces.push(sdr.product);
        }

        if (sdr?.tuner) {
            pieces.push(sdr.tuner);
        }

        const rate = formatRate(sdr?.sample_rate);

        if (rate) {
            pieces.push(rate);
        }

        if (pieces.length === 0 && sdr?.detail) {
            pieces.push(sdr.detail);
        }

        setText(
            "localSdrDetail",
            pieces.join(" · ") || "Receiver unavailable"
        );
    }

    function renderGps(gps) {
        const state = gps?.state || "no_device";

        setText(
            "localGpsState",
            stateLabel(state)
        );

        setIndicator(
            "localGpsIndicator",
            state
        );

        if (
            gps?.fix === true &&
            Number.isFinite(Number(gps.latitude)) &&
            Number.isFinite(Number(gps.longitude))
        ) {
            const lat = Number(gps.latitude).toFixed(5);
            const lon = Number(gps.longitude).toFixed(5);

            const detail = [
                `${lat}, ${lon}`,
                gps.altitude_m != null
                    ? `${Number(gps.altitude_m).toFixed(0)} m`
                    : null,
                gps.mode != null
                    ? `MODE ${gps.mode}`
                    : null,
            ]
                .filter(Boolean)
                .join(" · ");

            setText(
                "localGpsDetail",
                detail
            );

            return;
        }

        setText(
            "localGpsDetail",
            gps?.detail || "Position unavailable"
        );
    }

    function render(snapshot) {
        setText(
            "localSensorHost",
            snapshot?.host || "---"
        );

        renderSdr(snapshot?.sdr);
        renderGps(snapshot?.gps);

        setText(
            "localSensorRefresh",
            `UPDATED ${new Date().toLocaleTimeString()}`
        );
    }

    function renderError(error) {
        setText(
            "localSdrState",
            "ERROR"
        );

        setText(
            "localGpsState",
            "ERROR"
        );

        setIndicator(
            "localSdrIndicator",
            "error"
        );

        setIndicator(
            "localGpsIndicator",
            "error"
        );

        setText(
            "localSensorRefresh",
            `SENSOR API ERROR · ${error.message}`
        );
    }

    async function refresh() {
        try {
            const controller =
                new AbortController();

            const timeout =
                window.setTimeout(
                    () => controller.abort(),
                    10000
                );

            const response = await fetch(
                STATUS_URL,
                {
                    cache: "no-store",
                    signal: controller.signal,
                }
            );

            window.clearTimeout(timeout);

            if (!response.ok) {
                throw new Error(
                    `HTTP ${response.status}`
                );
            }

            const data = await response.json();

            render(data);
        } catch (error) {
            console.error(
                "Local sensor refresh failed:",
                error
            );

            renderError(error);
        }
    }

    function mount() {
        if (!el("localSensorPanel")) {
            console.warn(
                "Local Sensors panel not found"
            );

            return;
        }

        refresh();

        timer = window.setInterval(
            () => {
                if (!document.hidden) {
                    refresh();
                }
            },
            REFRESH_MS
        );
    }

    window.JarvisLocalSensors = {
        refresh,
    };

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            mount,
            { once: true }
        );
    } else {
        mount();
    }
})();
