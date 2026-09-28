(() => {
    "use strict";

    const HOME = {
        longitude: 12,
        latitude: 25,
        altitude: 18000000
    };

    const imageryProvider =
        new Cesium.OpenStreetMapImageryProvider({
            url: "https://tile.openstreetmap.org/"
        });

    const viewer = new Cesium.Viewer("cesiumContainer", {
        animation: false,
        timeline: false,
        baseLayerPicker: false,
        geocoder: false,
        homeButton: false,
        sceneModePicker: false,
        navigationHelpButton: false,
        fullscreenButton: false,
        infoBox: false,
        selectionIndicator: true,
        shouldAnimate: true,
        baseLayer: new Cesium.ImageryLayer(imageryProvider),
        terrainProvider: new Cesium.EllipsoidTerrainProvider()
    });

    viewer.scene.globe.enableLighting = true;

    // Earth must occlude markers on the far hemisphere.
    viewer.scene.globe.depthTestAgainstTerrain = true;

    function resetCamera() {
        viewer.camera.flyTo({
            destination: Cesium.Cartesian3.fromDegrees(
                HOME.longitude,
                HOME.latitude,
                HOME.altitude
            ),
            duration: 1.2
        });
    }

    viewer.camera.setView({
        destination: Cesium.Cartesian3.fromDegrees(
            HOME.longitude,
            HOME.latitude,
            HOME.altitude
        )
    });

    const groups = {
        incidents: [],
        nuclear: [],
        security: []
    };

    let lastData = null;
    let selectedRecord = null;

    function escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;");
    }

    function validLocation(item) {
        const loc = item?.location;

        if (!loc) return false;

        const lat = Number(loc.latitude);
        const lon = Number(loc.longitude);

        return Number.isFinite(lat) &&
               Number.isFinite(lon) &&
               lat >= -90 && lat <= 90 &&
               lon >= -180 && lon <= 180;
    }

    function severityColor(item, group) {
        if (group === "nuclear") {
            return Cesium.Color.fromCssColorString("#63efb7");
        }

        const severity =
            String(item.severity || "").toLowerCase();

        if (
            severity === "critical" ||
            severity === "emergency" ||
            severity === "severe"
        ) {
            return Cesium.Color.fromCssColorString("#ff3030");
        }

        if (severity === "high") {
            return Cesium.Color.fromCssColorString("#ef6868");
        }

        if (
            severity === "watch" ||
            severity === "medium" ||
            severity === "warning"
        ) {
            return Cesium.Color.fromCssColorString("#e4b65a");
        }

        if (group === "incidents") {
            return Cesium.Color.fromCssColorString("#e4b65a");
        }

        return Cesium.Color.fromCssColorString("#63efb7");
    }

    function pointSize(item, group) {
        if (group === "nuclear") return 5;

        const severity =
            String(item.severity || "").toLowerCase();

        if (
            severity === "critical" ||
            severity === "emergency" ||
            severity === "severe"
        ) return 11;

        if (severity === "high") return 9;
        if (severity === "watch") return 7;

        return 6;
    }

    function recordAgeHours(item) {
        if (Number.isFinite(Number(item.age_hours))) {
            return Number(item.age_hours);
        }

        const raw =
            item.published_at ||
            item.updated_at;

        if (!raw) return null;

        const timestamp = Date.parse(raw);

        if (!Number.isFinite(timestamp)) {
            return null;
        }

        return Math.max(
            0,
            (Date.now() - timestamp) / 3600000
        );
    }

    function passesAgeFilter(item, group) {
        if (group === "nuclear") {
            return true;
        }

        const maxHours =
            Number(document.getElementById("ageFilter").value);

        if (!maxHours) return true;

        const age = recordAgeHours(item);

        // Unknown age remains visible rather than silently discarded.
        if (age === null) return true;

        return age <= maxHours;
    }

    function addPoint(item, group) {
        if (!validLocation(item)) return null;
        if (!passesAgeFilter(item, group)) return null;

        const lat = Number(item.location.latitude);
        const lon = Number(item.location.longitude);

        const entity = viewer.entities.add({
            position: Cesium.Cartesian3.fromDegrees(lon, lat),

            point: {
                pixelSize: pointSize(item, group),
                color: severityColor(item, group),
                outlineColor: Cesium.Color.BLACK,
                outlineWidth: 1,

                scaleByDistance:
                    new Cesium.NearFarScalar(
                        1.0e5, 1.35,
                        2.0e7, 0.75
                    )
            },

            properties: {
                jarvisGroup: group,
                jarvisRecord: JSON.stringify(item)
            }
        });

        groups[group].push(entity);
        return entity;
    }

    function updateDisplayedCount() {
        const count =
            groups.incidents.length +
            groups.nuclear.length +
            groups.security.length;

        document.getElementById("displayedCount").textContent =
            count;
    }

    function renderSitrep(data) {
        lastData = data;

        viewer.entities.removeAll();

        groups.incidents = [];
        groups.nuclear = [];
        groups.security = [];

        const incidents =
            data.incidents || [];

        const nuclearSites =
            data.nuclear_sites || [];

        const securityEvents =
            data.security_events || [];

        for (const item of incidents) {
            addPoint(item, "incidents");
        }

        for (const item of nuclearSites) {
            addPoint(item, "nuclear");
        }

        for (const item of securityEvents) {
            addPoint(item, "security");
        }

        document.getElementById("incidentCount").textContent =
            groups.incidents.length;

        document.getElementById("nuclearCount").textContent =
            groups.nuclear.length;

        document.getElementById("securityCount").textContent =
            groups.security.length;

        document.getElementById("totalSecurityCount").textContent =
            securityEvents.length;

        document.getElementById("nuclearEventCount").textContent =
            (data.nuclear_events || []).length;

        document.getElementById("sourceCount").textContent =
            (data.sources || []).length;

        document.getElementById("errorCount").textContent =
            (data.errors || []).length;

        const state =
            data.operational_state || "UNKNOWN";

        document.getElementById("operationalState").textContent =
            state;

        document.getElementById("systemState").textContent =
            data.refreshing ? `${state} / REFRESHING` : state;

        document.getElementById("generatedAt").textContent =
            `SITREP ${data.generated_at || "UNKNOWN"}`;

        const indicator =
            document.getElementById("liveIndicator");

        indicator.classList.remove("live", "degraded");

        if (state === "LIVE" && !data.refreshing) {
            indicator.classList.add("live");
        } else if (
            state === "DEGRADED" ||
            (data.errors || []).length
        ) {
            indicator.classList.add("degraded");
        }

        updateDisplayedCount();
        applyLayerVisibility();
    }

    function applyLayerVisibility() {
        const mapping = {
            incidents: "layerIncidents",
            nuclear: "layerNuclear",
            security: "layerSecurity"
        };

        for (const [group, id] of Object.entries(mapping)) {
            const visible =
                document.getElementById(id).checked;

            for (const entity of groups[group]) {
                entity.show = visible;
            }
        }
    }

    for (const id of [
        "layerIncidents",
        "layerNuclear",
        "layerSecurity"
    ]) {
        document.getElementById(id)
            .addEventListener(
                "change",
                applyLayerVisibility
            );
    }

    document.getElementById("ageFilter")
        .addEventListener("change", () => {
            if (lastData) renderSitrep(lastData);
        });

    function sourceUrl(item) {
        if (item?.source?.url) return item.source.url;

        if (
            Array.isArray(item?.sources) &&
            item.sources[0]?.url
        ) {
            return item.sources[0].url;
        }

        return null;
    }

    function renderDetail(item) {
        selectedRecord = item;

        const detail =
            document.getElementById("eventDetail");

        const title =
            item.title ||
            item.name ||
            item.kind ||
            "JARVIS record";

        const source =
            item.source?.publisher ||
            item.sources?.[0]?.publisher ||
            "Unknown";

        const age =
            recordAgeHours(item);

        const ageText =
            age === null
                ? "—"
                : age < 1
                    ? "<1 hour"
                    : `${Math.round(age)} hours`;

        const url = sourceUrl(item);

        detail.innerHTML = `
            <div class="event-title">
                ${escapeHtml(title)}
            </div>

            <br>

            TYPE:
            ${escapeHtml(item.kind || "—")}
            <br>

            REGION:
            ${escapeHtml(item.region || "—")}
            <br>

            SEVERITY:
            ${escapeHtml(item.severity || "—")}
            <br>

            AGE:
            ${escapeHtml(ageText)}
            <br>

            SOURCE:
            ${escapeHtml(source)}

            <br><br>

            ${escapeHtml(item.summary || "")}

            <div class="event-actions">
                <button id="focusSelected">
                    FOCUS
                </button>

                ${
                    url
                        ? `<button id="openSource">SOURCE</button>`
                        : ""
                }
            </div>
        `;

        document.getElementById("focusSelected")
            ?.addEventListener("click", () => {
                focusRecord(item);
            });

        document.getElementById("openSource")
            ?.addEventListener("click", () => {
                window.open(
                    url,
                    "_blank",
                    "noopener,noreferrer"
                );
            });
    }

    function focusRecord(item) {
        if (!validLocation(item)) return;

        viewer.camera.flyTo({
            destination:
                Cesium.Cartesian3.fromDegrees(
                    Number(item.location.longitude),
                    Number(item.location.latitude),
                    1200000
                ),
            duration: 1.1
        });
    }

    viewer.selectedEntityChanged.addEventListener(entity => {
        const detail =
            document.getElementById("eventDetail");

        if (!entity?.properties) {
            selectedRecord = null;
            detail.textContent =
                "Select an object on the globe.";
            return;
        }

        try {
            const raw =
                entity.properties.jarvisRecord.getValue();

            renderDetail(JSON.parse(raw));
        } catch (error) {
            console.error(error);
            detail.textContent =
                "Unable to decode selected record.";
        }
    });

    document.getElementById("resetView")
        .addEventListener("click", resetCamera);

    document.getElementById("leftToggle")
        .addEventListener("click", () => {
            document.getElementById("leftPanel")
                .classList.toggle("hidden");
        });

    document.getElementById("rightToggle")
        .addEventListener("click", () => {
            document.getElementById("rightPanel")
                .classList.toggle("hidden");
        });

    viewer.camera.changed.addEventListener(() => {
        const p =
            viewer.camera.positionCartographic;

        const lat =
            Cesium.Math.toDegrees(p.latitude).toFixed(2);

        const lon =
            Cesium.Math.toDegrees(p.longitude).toFixed(2);

        const altitude =
            Math.round(p.height / 1000);

        document.getElementById("cameraPosition").textContent =
            `${lat}° ${lon}° / ${altitude} km`;
    });

    async function refresh() {
        try {
            const response =
                await fetch(
                    "/operations/sitrep",
                    { cache: "no-store" }
                );

            if (!response.ok) {
                throw new Error(
                    `HTTP ${response.status}`
                );
            }

            renderSitrep(await response.json());

        } catch (error) {
            console.error(
                "Global 3D SITREP refresh failed:",
                error
            );

            document.getElementById("systemState")
                .textContent = "DATA ERROR";

            const indicator =
                document.getElementById("liveIndicator");

            indicator.classList.remove("live");
            indicator.classList.add("degraded");

            // Deliberately leave last-known entities on-screen.
        }
    }

    refresh();

    // Operational display refresh.
    setInterval(refresh, 60000);
})();
