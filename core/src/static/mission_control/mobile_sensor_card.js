(() => {
    "use strict";

    const STATUS_API = "/api/sensors/mobile/status";
    const LATEST_API = "/api/sensors/mobile/latest";
    const REFRESH_MS = 5000;

    let timer = null;
    let observer = null;

    function byId(id) {
        return document.getElementById(id);
    }

    function finite(value) {
        const n = Number(value);
        return Number.isFinite(n) ? n : null;
    }

    function setText(id, value) {
        const node = byId(id);
        if (node) {
            node.textContent = value;
        }
    }

    function channelLive(status, name) {
        return status?.channels?.[name]?.state === "live";
    }

    function battery(latest) {
        const d = latest?.device || {};
        const n = finite(d.battery_level);

        if (n === null) {
            return String(
                d.battery_state || "—"
            ).toUpperCase();
        }

        return `${Math.max(
            0,
            Math.min(100, Math.round(n * 100))
        )}%`;
    }

    function temperature(latest) {
        return String(
            latest?.device?.thermal_state || "—"
        ).toUpperCase();
    }

    function proximity(latest) {
        const value = latest?.device?.proximity_near;

        if (value === true) return "NEAR";
        if (value === false) return "CLEAR";
        return "—";
    }

    function activity(latest) {
        const a = latest?.activity || {};

        if (a.automotive) return "AUTO";
        if (a.running) return "RUN";
        if (a.cycling) return "CYCLE";
        if (a.walking) return "WALK";
        if (a.stationary) return "STILL";

        return "—";
    }

    function steps(latest) {
        const n = finite(latest?.pedometer?.steps);
        return n === null ? "—" : String(Math.round(n));
    }

    function heading(status) {
        const n = finite(status?.heading_deg);
        return n === null ? "—" : `${n.toFixed(0)}°`;
    }

    function accuracy(status) {
        const n = finite(status?.horizontal_accuracy_m);
        return n === null ? "—" : `±${n.toFixed(1)}m`;
    }

    function altitude(status) {
        const n = finite(status?.altitude_m);
        return n === null ? "—" : `${n.toFixed(0)}m`;
    }

    function age(status) {
        const n = finite(status?.fix_age_seconds);
        return n === null ? "—" : `${n.toFixed(0)}s`;
    }

    function pressure(latest) {
        const n = finite(latest?.environment?.pressure_kpa);
        return n === null ? "—" : `${n.toFixed(1)}kPa`;
    }

    function relativeAltitude(latest) {
        const n = finite(latest?.environment?.relative_altitude_m);

        if (n === null) {
            return "—";
        }

        return `${n > 0 ? "+" : ""}${n.toFixed(1)}m`;
    }

    function findMount() {
        const direct = [
            "#command-center",
            "#commandCenter",
            "[data-view='command-center']",
            ".command-center",
            ".command-center-content",
            ".operations-center",
            ".operations-center-content",
            ".dashboard-grid",
            ".overview-grid",
            ".content-grid",
            ".main-content"
        ];

        for (const selector of direct) {
            const node = document.querySelector(selector);
            if (node) {
                return node;
            }
        }

        const headings = Array.from(
            document.querySelectorAll("h1,h2,h3")
        );

        const headingNode = headings.find((node) => {
            const t = String(node.textContent || "").toLowerCase();
            return (
                t.includes("executive operations center") ||
                t.includes("command center")
            );
        });

        if (headingNode?.parentElement) {
            return headingNode.parentElement;
        }

        return document.querySelector("main");
    }

    function createCard() {
        if (byId("mobileSensorCommandCard")) {
            return byId("mobileSensorCommandCard");
        }

        const mount = findMount();

        if (!mount) {
            return null;
        }

        const card = document.createElement("section");
        card.id = "mobileSensorCommandCard";
        card.className = "mobile-sensor-command-card";
        card.setAttribute(
            "aria-label",
            "iPhone mobile sensor status"
        );

        card.innerHTML = `
            <div class="mobile-sensor-command-head">
                <div>
                    <span>MOBILE SENSOR</span>
                    <strong id="mscNode">iphone14promax</strong>
                </div>
                <strong id="mscState">---</strong>
            </div>

            <div class="mobile-sensor-command-counts">
                <strong id="mscCounts">0 / 0 LIVE</strong>
                <span id="mscFaults">0 STALE · 0 NODATA</span>
            </div>

            <div class="mobile-sensor-command-grid">
                <div><span>GPS</span><strong id="mscGps">—</strong></div>
                <div><span>HDG</span><strong id="mscHeading">—</strong></div>
                <div><span>ALT</span><strong id="mscAltitude">—</strong></div>

                <div><span>FIX</span><strong id="mscFix">—</strong></div>
                <div><span>BARO</span><strong id="mscBaro">—</strong></div>
                <div><span>REL ALT</span><strong id="mscRelAlt">—</strong></div>

                <div><span>IMU</span><strong id="mscImu">—</strong></div>
                <div><span>ACT</span><strong id="mscActivity">—</strong></div>
                <div><span>STEPS</span><strong id="mscSteps">—</strong></div>

                <div><span>PWR</span><strong id="mscBattery">—</strong></div>
                <div><span>TEMP</span><strong id="mscThermal">—</strong></div>
                <div><span>PROX</span><strong id="mscProx">—</strong></div>
            </div>


            <!-- JARVIS_R16_MISSION_HEALTH -->
            <div class="msc-r16-health">
                <span>IMU CHANNELS</span>
                <strong id="mscR16Health">—</strong>
                <span>TELEMETRY</span>
                <strong id="mscR16Freshness">—</strong>
            </div>

            <div class="mobile-sensor-command-foot">
                <span id="mscGnssState">GNSS —</span>
                <span id="mscAge">LINK —</span>
            </div>
        `;

        const firstSubstantial =
            Array.from(mount.children).find(
                (node) =>
                    node.tagName !== "H1" &&
                    node.tagName !== "H2" &&
                    node.tagName !== "H3"
            );

        if (firstSubstantial) {
            mount.insertBefore(card, firstSubstantial);
        } else {
            mount.appendChild(card);
        }

        return card;
    }

    function render(status, latest) {
        const card = createCard();

        if (!card) {
            return;
        }

        const state = String(
            status?.state || "offline"
        ).toUpperCase();

        card.dataset.state =
            state === "ONLINE"
                ? "live"
                : state === "STALE"
                    ? "warn"
                    : "off";

        setText("mscState", state);
        setText("mscNode", status?.node_id || "MOBILE");

        const channels =
            status?.channels &&
            typeof status.channels === "object"
                ? Object.keys(status.channels)
                : [];

        const live = Array.isArray(status?.live_channels)
            ? status.live_channels.length
            : 0;

        const stale = Array.isArray(status?.stale_channels)
            ? status.stale_channels.length
            : 0;

        const noData = Array.isArray(status?.no_data_channels)
            ? status.no_data_channels.length
            : 0;

        setText(
            "mscCounts",
            `${live} / ${channels.length} LIVE`
        );

        setText(
            "mscFaults",
            `${stale} STALE · ${noData} NODATA`
        );

        setText("mscGps", accuracy(status));
        setText("mscHeading", heading(status));
        setText("mscAltitude", altitude(status));
        setText("mscFix", age(status));
        setText("mscBaro", pressure(latest));
        setText("mscRelAlt", relativeAltitude(latest));

        const imuNames = [
            "accelerometer",
            "gyroscope",
            "magnetometer",
            "device_motion"
        ];

        const imuLive = imuNames.filter(
            (name) => channelLive(status, name)
        ).length;

        setText(
            "mscImu",
            imuLive === 4 ? "LIVE" : `${imuLive}/4`
        );

        setText("mscActivity", activity(latest));
        setText("mscSteps", steps(latest));
        setText("mscBattery", battery(latest));
        setText("mscThermal", temperature(latest));
        setText("mscProx", proximity(latest));
        r16MissionRender(status);

        setText(
            "mscGnssState",
            channelLive(status, "gnss")
                ? "GNSS LIVE"
                : "GNSS CHECK"
        );

        const linkAge = finite(status?.age_seconds);

        setText(
            "mscAge",
            linkAge === null
                ? "LINK —"
                : `LINK ${linkAge.toFixed(1)}s`
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


    function r16MissionRender(status) {
        const names = [
            "accelerometer",
            "gyroscope",
            "magnetometer",
            "device_motion",
            "barometer",
            "absolute_altitude"
        ];
        const active = names.filter(n => channelLive(status, n)).length;
        const fresh = r16Fresh(status);

        setText(
            "mscR16Health",
            fresh ? `${active}/${names.length} LIVE` : "NOT LIVE"
        );
        setText(
            "mscR16Freshness",
            fresh
                ? `${r16Number(status.age_seconds, 1)}s AGO`
                : "STALE / OFFLINE"
        );
    }

    function renderError() {
        const card = createCard();

        if (!card) {
            return;
        }

        card.dataset.state = "off";
        setText("mscState", "LINK ERROR");
        setText("mscCounts", "0 / 0 LIVE");
        setText("mscFaults", "TELEMETRY UNAVAILABLE");

        [
            "mscGps",
            "mscHeading",
            "mscAltitude",
            "mscFix",
            "mscBaro",
            "mscRelAlt",
            "mscImu",
            "mscActivity",
            "mscSteps",
            "mscBattery",
            "mscThermal",
            "mscProx"
        ].forEach((id) => setText(id, "—"));

        setText("mscR16Health", "—");
        setText("mscR16Freshness", "LINK ERROR");
        setText("mscGnssState", "GNSS —");
        setText("mscAge", "LINK —");
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
        if (!byId("mobileSensorCommandCard")) {
            createCard();
        }

        try {
            const [status, latest] = await Promise.all([
                getJson(STATUS_API),
                getJson(LATEST_API)
            ]);

            render(status, latest);
        } catch (error) {
            console.warn(
                "[mobile-sensor-command-card-r3e] refresh failed:",
                error
            );
            renderError();
        }
    }

    function begin() {
        createCard();
        refresh();

        if (timer !== null) {
            window.clearInterval(timer);
        }

        timer = window.setInterval(
            refresh,
            REFRESH_MS
        );

        observer = new MutationObserver(() => {
            if (!byId("mobileSensorCommandCard")) {
                createCard();
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            begin,
            { once: true }
        );
    } else {
        begin();
    }
})();
