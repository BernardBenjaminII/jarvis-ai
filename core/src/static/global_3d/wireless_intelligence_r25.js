(() => {
    "use strict";

    const API = "/api/sensors";
    const REFRESH_MS = 15000;
    const MAX_DEVICES = 30;
    let active = false;

    function create(tag, cls, value) {
        const node = document.createElement(tag);
        if (cls) node.className = cls;
        if (value !== undefined) node.textContent = String(value);
        return node;
    }

    function field(parent, label, value) {
        const line = create("div", "wi-field");
        line.append(
            create("span", "wi-label", label),
            create("span", "wi-value", value)
        );
        parent.append(line);
    }

    function healthLabel(state) {
        return String(state || "unknown").toUpperCase();
    }

    function setStatus(node, state) {
        const normalized = String(state || "unknown");
        node.textContent = healthLabel(normalized);
        node.className = "wi-status " +
            (["online", "ready", "live"].includes(normalized)
                ? "wi-online"
                : normalized === "stale"
                    ? "wi-stale"
                    : "wi-offline");
    }

    function normalizeWifi(data) {
        if (Array.isArray(data)) return data;
        if (!data || typeof data !== "object") return [];

        if (Array.isArray(data.sensors)) return data.sensors;

        if (data.sensors && typeof data.sensors === "object") {
            return Object.entries(data.sensors).map(([id, value]) => ({
                sensor_id: id,
                ...(value && typeof value === "object" ? value : {})
            }));
        }

        if (Array.isArray(data.devices)) return data.devices;

        return Object.entries(data)
            .filter(([key]) => /^wifi-0[12]$/i.test(key))
            .map(([id, value]) => ({
                sensor_id: id,
                ...(value && typeof value === "object" ? value : {})
            }));
    }

    function fmtTime(value) {
        if (!value) return "—";
        const date = new Date(value);
        return Number.isNaN(date.getTime())
            ? "—"
            : date.toLocaleTimeString();
    }

    async function fetchJSON(path) {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 6000);
        try {
            const response = await fetch(API + path, {
                cache: "no-store",
                signal: controller.signal
            });
            if (!response.ok) {
                throw new Error("HTTP " + response.status);
            }
            return await response.json();
        } finally {
            clearTimeout(timeout);
        }
    }

    function createPanel() {
        const mount = document.getElementById("localSensorPanel");
        if (!mount || document.getElementById("jarvisWirelessR25")) {
            return false;
        }

        const panel = create("section", "wi-panel");
        panel.id = "jarvisWirelessR25";

        panel.append(create("h3", "", "WIRELESS INTELLIGENCE"));

        const summary = create("div", "wi-summary");
        summary.id = "wiSummary";
        summary.textContent = "Loading wireless sensors...";
        panel.append(summary);
        // JARVIS_WIRELESS_R26_LINK
        const workspaceLink = create("a", "wi-workspace-link",
                                      "OPEN WIRELESS WORKSPACE →");
        workspaceLink.href =
            "/static/global_3d/wireless_workspace.html";
        panel.append(workspaceLink);


        const sensors = create("div", "wi-sensors");

        for (const [name, id] of [
            ["ESP32-C6 / IOT-01", "iot"],
            ["AR9271 / WIFI-01", "wifi1"],
            ["RTL8814AU / WIFI-02", "wifi2"]
        ]) {
            const card = create("div", "wi-sensor");
            card.append(create("strong", "", name));

            const status = create("span", "wi-status", "LOADING");
            status.id = "wi-" + id + "-status";
            card.append(status);

            const details = create("div", "wi-detail");
            details.id = "wi-" + id + "-detail";
            card.append(details);
            sensors.append(card);
        }

        panel.append(sensors);

        const heading = create("h4", "", "RECENT BLE OBSERVATIONS");
        panel.append(heading);

        const deviceList = create("div", "wi-devices");
        deviceList.id = "wiDeviceList";
        deviceList.textContent = "Waiting for observations...";
        panel.append(deviceList);

        const footer = create("div", "wi-footer");
        footer.id = "wiUpdated";
        panel.append(footer);

        mount.append(panel);
        return true;
    }

    async function refresh() {
        if (active) return;
        active = true;

        const results = await Promise.allSettled([
            fetchJSON("/iot/status"),
            fetchJSON("/iot/summary"),
            fetchJSON("/iot/devices?minutes=5&limit=" + MAX_DEVICES),
            fetchJSON("/wifi/status")
        ]);

        const [health, summary, devices, wifi] = results;
        const ok = result => result.status === "fulfilled"
            ? result.value : null;

        const status = ok(health);
        const metrics = ok(summary);
        const ble = ok(devices);
        const wifiData = ok(wifi);

        const iotStatus = document.getElementById("wi-iot-status");
        const iotDetail = document.getElementById("wi-iot-detail");
        const summaryNode = document.getElementById("wiSummary");
        const list = document.getElementById("wiDeviceList");

        if (iotStatus) {
            setStatus(iotStatus, status?.state || "unavailable");
        }

        if (iotDetail) {
            iotDetail.replaceChildren();
            field(iotDetail, "Firmware", status?.firmware || "—");
            field(iotDetail, "Heartbeat",
                status?.age_seconds == null
                    ? "—"
                    : status.age_seconds + "s ago");
        }

        if (summaryNode) {
            summaryNode.textContent =
                (metrics?.observations ?? "—") + " stored observations · " +
                (metrics?.distinct_addresses ?? "—") + " retained addresses · " +
                (ble?.devices?.length ?? "—") + " recently seen";
        }

        const wifiSensors = normalizeWifi(wifiData);

        for (const [sensorID, slot] of [
            ["WIFI-01", "wifi1"],
            ["WIFI-02", "wifi2"]
        ]) {
            const found = wifiSensors.find(item =>
                String(item.sensor_id || item.id || item.name || "")
                    .toUpperCase() === sensorID
            );

            const stateNode =
                document.getElementById("wi-" + slot + "-status");
            const detailNode =
                document.getElementById("wi-" + slot + "-detail");

            if (stateNode) {
                setStatus(stateNode,
                    found?.state || found?.status ||
                    (found?.ready === true ? "ready" : "unknown"));
            }

            if (detailNode) {
                detailNode.textContent =
                    found?.interface || found?.iface ||
                    found?.device || (
                        wifiData ? "Inventory available" : "API unavailable"
                    );
            }
        }

        if (list) {
            list.replaceChildren();
            const rows = Array.isArray(ble?.devices) ? ble.devices : [];

            if (rows.length === 0) {
                list.append(create(
                    "div", "wi-empty",
                    ble ? "No BLE observations in the last 5 minutes"
                        : "BLE observations unavailable"
                ));
            }

            for (const device of rows) {
                const item = create("div", "wi-device");
                const name = device.advertised_name ||
                    "Unnamed BLE advertiser";

                item.append(create("strong", "wi-device-name", name));
                item.append(create(
                    "div", "wi-address",
                    device.address || "Unknown address"
                ));

                const meta = [
                    device.avg_rssi == null
                        ? null : device.avg_rssi + " dBm",
                    device.sightings == null
                        ? null : device.sightings + " sightings",
                    fmtTime(device.last_seen)
                ].filter(Boolean);

                item.append(create("div", "wi-device-meta",
                    meta.join(" · ")));
                list.append(item);
            }
        }

        const updated = document.getElementById("wiUpdated");
        if (updated) {
            updated.textContent =
                "Passive monitoring · Updated " +
                new Date().toLocaleTimeString();
        }

        active = false;
    }

    function start() {
        if (!createPanel()) return;
        refresh();
        setInterval(refresh, REFRESH_MS);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", start, {once: true});
    } else {
        start();
    }
})();
