(() => {
    "use strict";

    const STATUS_API = "/api/sensors/mobile/status";
    const LATEST_API = "/api/sensors/mobile/latest";
    const REFRESH_MS = 5000;

    let timer = null;

    function byId(id) {
        return document.getElementById(id);
    }

    function finite(value) {
        const n = Number(value);
        return Number.isFinite(n) ? n : null;
    }

    function text(id, value) {
        const node = byId(id);
        if (node) {
            node.textContent = value;
        }
    }

    function stateClass(state) {
        const s = String(state || "").toLowerCase();

        if (s === "online" || s === "live" || s === "ready") {
            return "live";
        }

        if (s === "stale" || s === "warning") {
            return "warn";
        }

        return "off";
    }

    function channelLive(status, name) {
        return status?.channels?.[name]?.state === "live";
    }

    function allLive(status, names) {
        return names.every((name) => channelLive(status, name));
    }

    function formatHeading(value) {
        const n = finite(value);
        return n === null ? "—" : `${n.toFixed(0)}°`;
    }

    function formatAccuracy(value) {
        const n = finite(value);
        return n === null ? "—" : `±${n.toFixed(1)} m`;
    }

    function formatAltitude(value) {
        const n = finite(value);
        return n === null ? "—" : `${n.toFixed(0)} m`;
    }

    function formatAge(value) {
        const n = finite(value);
        return n === null ? "—" : `${n.toFixed(0)} s`;
    }

    function formatPressure(latest) {
        const n = finite(latest?.environment?.pressure_kpa);
        return n === null ? "—" : `${n.toFixed(1)} kPa`;
    }

    function formatRelativeAltitude(latest) {
        const n = finite(latest?.environment?.relative_altitude_m);

        if (n === null) {
            return "—";
        }

        const sign = n > 0 ? "+" : "";
        return `${sign}${n.toFixed(1)} m`;
    }

    function activityLabel(latest) {
        const a = latest?.activity;

        if (!a || typeof a !== "object") {
            return "—";
        }

        if (a.automotive) return "AUTO";
        if (a.running) return "RUN";
        if (a.cycling) return "CYCLE";
        if (a.walking) return "WALK";
        if (a.stationary) return "STILL";
        return "UNKNOWN";
    }

    function stepsLabel(latest) {
        const steps = finite(latest?.pedometer?.steps);
        return steps === null ? "—" : String(Math.round(steps));
    }

    function batteryLabel(latest) {
        const d = latest?.device || {};
        const level = finite(d.battery_level);

        if (level === null) {
            return String(d.battery_state || "—").toUpperCase();
        }

        const pct = Math.max(
            0,
            Math.min(100, Math.round(level * 100))
        );

        return `${pct}% ${String(
            d.battery_state || ""
        ).toUpperCase()}`.trim();
    }

    function thermalLabel(latest) {
        return String(
            latest?.device?.thermal_state || "—"
        ).toUpperCase();
    }

    function proximityLabel(latest) {
        const value = latest?.device?.proximity_near;

        if (value === true) return "NEAR";
        if (value === false) return "CLEAR";
        return "—";
    }

    function createPanel() {
        if (byId("mobileSensorR3dPanel")) {
            return byId("mobileSensorR3dPanel");
        }

        const host = byId("localSensorPanel");

        if (!host) {
            return null;
        }

        const panel = document.createElement("div");
        panel.id = "mobileSensorR3dPanel";
        panel.className = "mobile-sensor-r3d";

        panel.innerHTML = `
            <div class="mobile-sensor-r3d-head">
                <span>MOBILE NODE</span>
                <strong id="mobileSensorR3dState">---</strong>
            </div>

            <div
                id="mobileSensorR3dNode"
                class="mobile-sensor-r3d-node">
                iphone14promax
            </div>

            <div class="mobile-sensor-r3d-grid">
                <div>
                    <span>POS</span>
                    <strong id="mobileSensorR3dPos">---</strong>
                </div>
                <div>
                    <span>HDG</span>
                    <strong id="mobileSensorR3dHeading">---</strong>
                </div>
                <div>
                    <span>ALT</span>
                    <strong id="mobileSensorR3dAltitude">---</strong>
                </div>
                <div>
                    <span>FIX</span>
                    <strong id="mobileSensorR3dFix">---</strong>
                </div>
                <div>
                    <span>IMU</span>
                    <strong id="mobileSensorR3dImu">---</strong>
                </div>
                <div>
                    <span>BARO</span>
                    <strong id="mobileSensorR3dBaro">---</strong>
                </div>
                <div>
                    <span>REL ALT</span>
                    <strong id="mobileSensorR3dRelAlt">---</strong>
                </div>
                <div>
                    <span>ACT</span>
                    <strong id="mobileSensorR3dActivity">---</strong>
                </div>
                <div>
                    <span>STEPS</span>
                    <strong id="mobileSensorR3dSteps">---</strong>
                </div>
                <div>
                    <span>PWR</span>
                    <strong id="mobileSensorR3dPower">---</strong>
                </div>
                <div>
                    <span>TEMP</span>
                    <strong id="mobileSensorR3dThermal">---</strong>
                </div>
                <div>
                    <span>PROX</span>
                    <strong id="mobileSensorR3dProx">---</strong>
                </div>
            </div>


            <!-- JARVIS_R16_GLOBAL_DETAIL -->
            <details class="mobile-r16-detail">
                <summary>LIVE MOTION & ENVIRONMENT</summary>
                <div class="mobile-r16-heading">
                    <span>TELEMETRY STATUS</span>
                    <strong id="mobileR16Fresh">—</strong>
                </div>
                <div class="mobile-r16-rows">
                    <div><span>ACCEL · g (X/Y/Z)</span><strong id="mobileR16Accel">—</strong></div>
                    <div><span>GYRO · rad/s (X/Y/Z)</span><strong id="mobileR16Gyro">—</strong></div>
                    <div><span>MAG · µT (X/Y/Z)</span><strong id="mobileR16Mag">—</strong></div>
                    <div><span>ROLL · rad</span><strong id="mobileR16Roll">—</strong></div>
                    <div><span>PITCH · rad</span><strong id="mobileR16Pitch">—</strong></div>
                    <div><span>YAW · rad</span><strong id="mobileR16Yaw">—</strong></div>
                    <div><span>PRESSURE · kPa</span><strong id="mobileR16Pressure">—</strong></div>
                    <div><span>ABS ALT · m</span><strong id="mobileR16AbsAlt">—</strong></div>
                </div>
            </details>

            <div class="mobile-sensor-r3d-foot">
                <span id="mobileSensorR3dCounts">
                    0 LIVE · 0 STALE · 0 NODATA
                </span>
            </div>
        `;

        const refresh =
            host.querySelector(".local-sensor-refresh");

        if (refresh) {
            host.insertBefore(panel, refresh);
        } else {
            host.appendChild(panel);
        }

        return panel;
    }

    function render(status, latest) {
        const panel = createPanel();

        if (!panel) {
            return;
        }

        const rootState = String(status?.state || "offline");
        panel.dataset.state = stateClass(rootState);

        text(
            "mobileSensorR3dState",
            rootState.toUpperCase()
        );

        text(
            "mobileSensorR3dNode",
            status?.node_id || "MOBILE"
        );

        text(
            "mobileSensorR3dPos",
            channelLive(status, "gnss")
                ? formatAccuracy(status?.horizontal_accuracy_m)
                : "CHECK"
        );

        text(
            "mobileSensorR3dHeading",
            channelLive(status, "compass")
                ? formatHeading(status?.heading_deg)
                : "CHECK"
        );

        text(
            "mobileSensorR3dAltitude",
            formatAltitude(status?.altitude_m)
        );

        text(
            "mobileSensorR3dFix",
            formatAge(status?.fix_age_seconds)
        );

        const imuNames = [
            "accelerometer",
            "gyroscope",
            "magnetometer",
            "device_motion"
        ];

        const imuCount = imuNames.filter(
            (name) => channelLive(status, name)
        ).length;

        text(
            "mobileSensorR3dImu",
            allLive(status, imuNames)
                ? "LIVE 4/4"
                : `${imuCount}/4`
        );

        text(
            "mobileSensorR3dBaro",
            formatPressure(latest)
        );

        text(
            "mobileSensorR3dRelAlt",
            formatRelativeAltitude(latest)
        );

        text(
            "mobileSensorR3dActivity",
            activityLabel(latest)
        );

        text(
            "mobileSensorR3dSteps",
            stepsLabel(latest)
        );

        text(
            "mobileSensorR3dPower",
            batteryLabel(latest)
        );

        text(
            "mobileSensorR3dThermal",
            thermalLabel(latest)
        );

        text(
            "mobileSensorR3dProx",
            proximityLabel(latest)
        );

        r16GlobalRender(status, latest);

        const live = Array.isArray(status?.live_channels)
            ? status.live_channels.length
            : 0;

        const stale = Array.isArray(status?.stale_channels)
            ? status.stale_channels.length
            : 0;

        const noData = Array.isArray(status?.no_data_channels)
            ? status.no_data_channels.length
            : 0;

        text(
            "mobileSensorR3dCounts",
            `${live} LIVE · ${stale} STALE · ${noData} NODATA`
        );
    }


    // JARVIS_R16_SENSOR_HELPERS
    function r16Fresh(status) {
        const age = status?.age_seconds;
        return String(status?.state || "").toLowerCase() === "online"
            && age !== null
            && age !== undefined
            && Number.isFinite(Number(age))
            && Number(age) >= 0
            && Number(age) <= 15;
    }

    function r16Number(value, digits = 2) {
        if (value === null || value === undefined || value === "") {
            return "—";
        }
        const n = Number(value);
        return Number.isFinite(n) ? n.toFixed(digits) : "—";
    }

    function r16Vector(object, keys, digits = 2) {
        if (!object || keys.some(k => object[k] == null)) {
            return "—";
        }
        return keys.map(k => r16Number(object[k], digits)).join(" / ");
    }

    function r16SensorText(status, channel, value) {
        if (!r16Fresh(status)) return "STALE";
        if (!channelLive(status, channel)) return "NO DATA";
        return value === "—" ? "NO DATA" : value;
    }


    function r16GlobalRender(status, latest) {
        const raw = latest?.raw || {};
        const motion = latest?.motion || {};
        const env = latest?.environment || {};
        const fresh = r16Fresh(status);

        const values = [
            ["mobileR16Accel", "accelerometer",
                r16Vector(raw.accelerometer, ["x_g", "y_g", "z_g"])],
            ["mobileR16Gyro", "gyroscope",
                r16Vector(raw.gyroscope, ["x_rad_s", "y_rad_s", "z_rad_s"])],
            ["mobileR16Mag", "magnetometer",
                r16Vector(raw.magnetometer, ["x_uT", "y_uT", "z_uT"])],
            ["mobileR16Roll", "device_motion",
                r16Number(motion.attitude?.roll_rad)],
            ["mobileR16Pitch", "device_motion",
                r16Number(motion.attitude?.pitch_rad)],
            ["mobileR16Yaw", "device_motion",
                r16Number(motion.attitude?.yaw_rad)],
            ["mobileR16Pressure", "barometer",
                r16Number(env.pressure_kpa, 3)],
            ["mobileR16AbsAlt", "absolute_altitude",
                r16Number(env.absolute_altitude_m, 1)]
        ];

        values.forEach(([id, channel, value]) => {
            text(id, r16SensorText(status, channel, value));
        });

        text(
            "mobileR16Fresh",
            fresh
                ? `LIVE · ${r16Number(status.age_seconds, 1)}s`
                : "STALE / OFFLINE"
        );
    }

    function renderError() {
        const panel = createPanel();

        if (!panel) {
            return;
        }

        panel.dataset.state = "off";

        text("mobileSensorR3dState", "LINK ERROR");
        text("mobileR16Fresh", "LINK ERROR");
        [
            "mobileR16Accel", "mobileR16Gyro", "mobileR16Mag",
            "mobileR16Roll", "mobileR16Pitch", "mobileR16Yaw",
            "mobileR16Pressure", "mobileR16AbsAlt"
        ].forEach(id => text(id, "—"));

        [
            "mobileSensorR3dPos",
            "mobileSensorR3dHeading",
            "mobileSensorR3dAltitude",
            "mobileSensorR3dFix",
            "mobileSensorR3dImu",
            "mobileSensorR3dBaro",
            "mobileSensorR3dRelAlt",
            "mobileSensorR3dActivity",
            "mobileSensorR3dSteps",
            "mobileSensorR3dPower",
            "mobileSensorR3dThermal",
            "mobileSensorR3dProx"
        ].forEach((id) => text(id, "—"));

        text(
            "mobileSensorR3dCounts",
            "TELEMETRY UNAVAILABLE"
        );
    }

    async function getJson(url) {
        const response = await fetch(url, {
            cache: "no-store",
            headers: {
                Accept: "application/json"
            }
        });

        if (!response.ok) {
            throw new Error(`${url}: HTTP ${response.status}`);
        }

        return response.json();
    }

    async function refresh() {
        try {
            const [status, latest] = await Promise.all([
                getJson(STATUS_API),
                getJson(LATEST_API)
            ]);

            render(status, latest);
        } catch (error) {
            console.warn(
                "[mobile-sensor-r3e] refresh failed:",
                error
            );
            renderError();
        }
    }

    function start() {
        createPanel();
        refresh();

        if (timer !== null) {
            window.clearInterval(timer);
        }

        timer = window.setInterval(
            refresh,
            REFRESH_MS
        );
    }

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            start,
            { once: true }
        );
    } else {
        start();
    }
})();
