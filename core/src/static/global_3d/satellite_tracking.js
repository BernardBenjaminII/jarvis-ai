(() => {
    "use strict";

    const ENDPOINT =
        "/operations/space/satellites";

    /*
     * CelesTrak elements are cached server-side for 15 minutes.
     * Jarvis still re-propagates them to the current time on each
     * request, so we can update displayed positions frequently
     * without repeatedly downloading orbital elements.
     */
    const REFRESH_MS = 15000;

    const OBSERVER_STORAGE_KEY =
        "jarvis.space.observer.r89d";

    const OBSERVER_REFRESH_MS =
        60000;

    let viewer = null;
    let mounted = false;
    let timer = null;

    /*
     * Satellites MUST NOT live in viewer.entities.
     *
     * Global 3D's SITREP renderer periodically calls
     * viewer.entities.removeAll(), which would erase every satellite.
     *
     * A dedicated CustomDataSource isolates orbital objects from
     * normal SITREP refreshes while retaining normal Cesium Entity
     * picking/selection behavior.
     */
    let satelliteSource = null;
    let selectedTrackEntity = null;
    let selectedTrackNorad = null;
    let observer = null;
    let observerTimer = null;
    let selectedSatelliteRecord = null;

    const entities = new Map();

    const GROUPS = {
        stations: {
            checkbox: "layerSatStations",
            count: "satStationCount",
            state: "satellites_stations"
        },

        gps: {
            checkbox: "layerSatGps",
            count: "satGpsCount",
            state: "satellites_gps"
        },

        weather: {
            checkbox: "layerSatWeather",
            count: "satWeatherCount",
            state: "satellites_weather"
        }
    };



    function loadObserver() {
        try {
            const raw =
                window.localStorage.getItem(
                    OBSERVER_STORAGE_KEY
                );

            if (!raw) {
                return null;
            }

            const parsed =
                JSON.parse(raw);

            const latitude =
                Number(parsed.latitude);

            const longitude =
                Number(parsed.longitude);

            const altitude_m =
                Number(
                    parsed.altitude_m || 0
                );

            if (
                !Number.isFinite(latitude) ||
                !Number.isFinite(longitude)
            ) {
                return null;
            }

            return {
                latitude,
                longitude,
                altitude_m:
                    Number.isFinite(
                        altitude_m
                    )
                        ? altitude_m
                        : 0
            };

        } catch {
            return null;
        }
    }


    function saveObserver(value) {
        observer = value;

        window.localStorage.setItem(
            OBSERVER_STORAGE_KEY,
            JSON.stringify(value)
        );
    }


    function observerQuery() {
        if (!observer) {
            return null;
        }

        const params =
            new URLSearchParams({
                lat:
                    String(
                        observer.latitude
                    ),

                lon:
                    String(
                        observer.longitude
                    ),

                alt_m:
                    String(
                        observer.altitude_m || 0
                    ),

                min_elevation_deg:
                    "0"
            });

        return params;
    }


    function formatUtc(iso) {
        if (!iso) {
            return "—";
        }

        const value =
            new Date(iso);

        if (
            Number.isNaN(
                value.getTime()
            )
        ) {
            return iso;
        }

        return value
            .toLocaleString();
    }


    async function refreshObserverSummary() {
        if (!observer) {
            text(
                "satObserverStatus",
                "Observer location unavailable"
            );

            return;
        }

        const params =
            observerQuery();

        try {
            const response =
                await fetch(
                    `/operations/space/observer?${params}`,
                    {
                        cache: "no-store"
                    }
                );

            if (!response.ok) {
                throw new Error(
                    `HTTP ${response.status}`
                );
            }

            const data =
                await response.json();

            const gps =
                data?.counts?.gps ?? 0;

            const stations =
                data?.counts?.stations ?? 0;

            const weather =
                data?.counts?.weather ?? 0;

            text(
                "satObserverStatus",
                `ABOVE HORIZON ${data.visible_total} • GPS ${gps} • STA ${stations} • WX ${weather}`
            );

        } catch (error) {
            text(
                "satObserverStatus",
                `OBSERVER ERROR • ${error.message}`
            );
        }
    }


    function requestBrowserLocation() {
        if (
            !navigator.geolocation
        ) {
            text(
                "satObserverStatus",
                "Browser location unavailable"
            );

            return;
        }

        text(
            "satObserverStatus",
            "Requesting observer location..."
        );

        navigator.geolocation
            .getCurrentPosition(
                position => {
                    saveObserver({
                        latitude:
                            position.coords.latitude,

                        longitude:
                            position.coords.longitude,

                        altitude_m:
                            Number.isFinite(
                                position.coords.altitude
                            )
                                ? position.coords.altitude
                                : 0
                    });

                    refreshObserverSummary();

                    if (
                        selectedSatelliteRecord
                    ) {
                        refreshSelectedPass(
                            selectedSatelliteRecord
                        );
                    }
                },

                error => {
                    text(
                        "satObserverStatus",
                        `LOCATION ${error.message}`
                    );
                },

                {
                    enableHighAccuracy:
                        true,

                    maximumAge:
                        30000,

                    timeout:
                        10000
                }
            );
    }


    async function refreshSelectedPass(
        record
    ) {
        selectedSatelliteRecord =
            record;

        const panel =
            document.getElementById(
                "satellitePassInfo"
            );

        if (!panel) {
            return;
        }

        if (!observer) {
            panel.innerHTML =
                "OBSERVER: use location to calculate pass";

            return;
        }

        const norad =
            Number(
                record?.norad_id
            );

        if (
            !Number.isFinite(norad)
        ) {
            return;
        }

        const params =
            observerQuery();

        params.set(
            "hours",
            "24"
        );

        try {
            panel.innerHTML =
                "PASS: calculating...";

            const response =
                await fetch(
                    `/operations/space/satellites/${norad}/pass?${params}`,
                    {
                        cache: "no-store"
                    }
                );

            if (!response.ok) {
                throw new Error(
                    `HTTP ${response.status}`
                );
            }

            const data =
                await response.json();

            const current =
                data.current || {};

            const pass =
                data.next_pass;

            const currentLine =
                `AZ ${Number(current.azimuth_deg).toFixed(1)}° • EL ${Number(current.elevation_deg).toFixed(1)}° • RANGE ${Math.round(Number(current.range_km))} km`;

            if (!pass) {
                panel.innerHTML = `
                    <br>
                    OBSERVER<br>
                    ${currentLine}<br>
                    NEXT PASS: none within prediction window
                `;

                return;
            }

            panel.innerHTML = `
                <br>
                OBSERVER<br>
                ${currentLine}<br>
                RISE:
                ${formatUtc(pass.rise_time)}
                @ ${pass.rise_azimuth_deg ?? "—"}°<br>
                PEAK:
                ${formatUtc(pass.peak_time)}
                • ${pass.max_elevation_deg ?? "—"}°<br>
                SET:
                ${formatUtc(pass.set_time)}
                @ ${pass.set_azimuth_deg ?? "—"}°
            `;

        } catch (error) {
            panel.innerHTML =
                `<br>PASS ERROR: ${error.message}`;
        }
    }


    function geo() {
        return window.JARVIS_GEOSPATIAL;
    }


    function el(id) {
        return document.getElementById(id);
    }


    function text(id, value) {
        const node = el(id);

        if (node) {
            node.textContent = value;
        }
    }


    function enabled(group) {
        const config = GROUPS[group];
        const node = el(config.checkbox);

        return node
            ? node.checked
            : true;
    }


    /*
     * CelesTrak's STATIONS group contains attached modules and
     * historical/debris objects in addition to useful independent
     * stations.
     *
     * Keep the full backend record set, but avoid putting multiple
     * coincident ISS modules and debris markers on the operational
     * globe.
     */
    function usefulStation(record) {
        const name =
            String(record?.name || "")
                .toUpperCase();

        if (name.includes("DEB")) {
            return false;
        }

        if (
            name === "ISS (ZARYA)" ||
            name === "CSS (TIANHE)"
        ) {
            return true;
        }

        /*
         * Preserve other genuinely independent stations if
         * CelesTrak adds them later.
         */
        return (
            name.includes("SPACE STATION") ||
            name.includes("TIANGONG")
        );
    }


    function visibleRecords(
        group,
        records
    ) {
        if (!Array.isArray(records)) {
            return [];
        }

        if (group === "stations") {
            return records.filter(
                usefulStation
            );
        }

        return records;
    }



    function satellitePriority(group, record) {
        const name =
            String(record?.name || "")
                .toUpperCase();

        if (
            name === "ISS (ZARYA)" ||
            name.includes(
                "INTERNATIONAL SPACE STATION"
            )
        ) {
            return "critical";
        }

        if (
            name === "CSS (TIANHE)" ||
            name.includes("TIANGONG")
        ) {
            return "high";
        }

        if (group === "gps") {
            return "navigation";
        }

        if (group === "weather") {
            const highValueNames = [
                "SENTINEL",
                "NOAA",
                "METEOR",
                "METEOSAT",
                "GOES",
                "FENGYUN",
                "HIMAWARI",
                "DMSP",
                "SUOMI",
                "JPSS"
            ];

            if (
                highValueNames.some(
                    value => name.includes(value)
                )
            ) {
                return "high";
            }
        }

        return "normal";
    }


    function isHighValue(group, record) {
        const priority =
            satellitePriority(
                group,
                record
            );

        return (
            priority === "critical" ||
            priority === "high"
        );
    }


    function highValueOnlyEnabled() {
        return (
            document
                .getElementById(
                    "satHighValueOnly"
                )
                ?.checked === true
        );
    }


    function satelliteColor(group, record) {
        const priority =
            satellitePriority(
                group,
                record
            );

        if (priority === "critical") {
            return Cesium.Color
                .fromCssColorString(
                    "#ffd34d"
                );
        }

        if (
            priority === "high" &&
            group === "stations"
        ) {
            return Cesium.Color
                .fromCssColorString(
                    "#fff2a8"
                );
        }

        if (
            priority === "high" &&
            group === "weather"
        ) {
            return Cesium.Color
                .fromCssColorString(
                    "#ba78ff"
                );
        }

        if (group === "stations") {
            return Cesium.Color.WHITE;
        }

        if (group === "gps") {
            return Cesium.Color
                .fromCssColorString(
                    "#61d9ff"
                );
        }

        return Cesium.Color
            .fromCssColorString(
                "#77ef9e"
            );
    }


    function satelliteSize(group, record) {
        const priority =
            satellitePriority(
                group,
                record
            );

        if (priority === "critical") {
            return 14;
        }

        if (priority === "high") {
            return 9;
        }

        if (group === "stations") {
            return 8;
        }

        return 6;
    }


    function altitudeMeters(record) {
        const value =
            Number(record?.altitude_km);

        return Number.isFinite(value)
            ? value * 1000
            : 0;
    }


    function position(record) {
        const lon =
            Number(record?.longitude);

        const lat =
            Number(record?.latitude);

        const altitude =
            altitudeMeters(record);

        if (
            !Number.isFinite(lon) ||
            !Number.isFinite(lat)
        ) {
            return null;
        }

        return Cesium.Cartesian3.fromDegrees(
            lon,
            lat,
            altitude
        );
    }


    function entityKey(group, record) {
        return `${group}:${record.norad_id}`;
    }


    function dossierRecord(
        group,
        record
    ) {
        return {
            kind: "satellite",
            title: record.name,
            name: record.name,

            severity: "informational",

            satellite_group: group,

            priority:
                satellitePriority(
                    group,
                    record
                ),

            norad_id: record.norad_id,
            object_id: record.object_id,

            altitude_km:
                record.altitude_km,

            velocity_km_s:
                record.velocity_km_s,

            inclination_deg:
                record.inclination_deg,

            eccentricity:
                record.eccentricity,

            period_minutes:
                record.period_minutes,

            element_epoch:
                record.element_epoch,

            element_age_hours:
                record.element_age_hours,

            position_time:
                record.position_time,

            location: {
                latitude:
                    record.latitude,

                longitude:
                    record.longitude
            },

            source: {
                publisher: "CelesTrak",
                url:
                    "https://celestrak.org/"
            }
        };
    }


    function createEntity(
        group,
        record
    ) {
        const pos = position(record);

        if (!pos) {
            return null;
        }

        const color =
            satelliteColor(
                group,
                record
            );

        const priority =
            satellitePriority(
                group,
                record
            );

        if (!satelliteSource) {
            return null;
        }

        const entity =
            satelliteSource.entities.add({
                name: record.name,

                position: pos,

                point: {
                    pixelSize:
                        satelliteSize(
                            group,
                            record
                        ),

                    color,

                    outlineColor:
                        priority === "critical"
                            ? Cesium.Color
                                .fromCssColorString(
                                    "#fff4b0"
                                )
                            : Cesium.Color.BLACK,

                    outlineWidth:
                        priority === "critical"
                            ? 3
                            : priority === "high"
                                ? 2
                                : 1,

                    scaleByDistance:
                        new Cesium.NearFarScalar(
                            1.0e5,
                            1.3,
                            5.0e7,
                            0.65
                        ),

                    disableDepthTestDistance:
                        Number.POSITIVE_INFINITY
                },

                label: {
                    text:
                        priority === "critical"
                            ? "ISS"
                            : (
                                priority === "high" &&
                                group === "stations"
                            )
                                ? record.name
                                : "",

                    font:
                        "11px monospace",

                    fillColor: color,

                    outlineColor:
                        Cesium.Color.BLACK,

                    outlineWidth: 2,

                    style:
                        Cesium.LabelStyle
                            .FILL_AND_OUTLINE,

                    pixelOffset:
                        new Cesium.Cartesian2(
                            10,
                            -8
                        ),

                    showBackground: true,

                    backgroundColor:
                        Cesium.Color.BLACK
                            .withAlpha(0.55),

                    scaleByDistance:
                        new Cesium.NearFarScalar(
                            1.0e5,
                            1.0,
                            3.0e7,
                            0.45
                        )
                },

                properties: {
                    jarvisGroup:
                        `satellite_${group}`,

                    jarvisRecord:
                        JSON.stringify(
                            dossierRecord(
                                group,
                                record
                            )
                        )
                },

                show:
                    enabled(group) &&
                    (
                        !highValueOnlyEnabled() ||
                        isHighValue(
                            group,
                            record
                        )
                    )
            });

        return entity;
    }


    function updateEntity(
        entity,
        group,
        record
    ) {
        const pos =
            position(record);

        if (!pos) {
            return;
        }

        /*
         * Updating the Cartesian location every 15 seconds gives
         * visible orbital motion while keeping the implementation
         * lightweight. We can later move propagation client-side
         * for smooth sub-second animation if desired.
         */
        entity.position = pos;

        const priority =
            satellitePriority(
                group,
                record
            );

        entity.show =
            enabled(group) &&
            (
                !highValueOnlyEnabled() ||
                isHighValue(
                    group,
                    record
                )
            );

        entity.point.pixelSize =
            satelliteSize(
                group,
                record
            );

        entity.point.color =
            satelliteColor(
                group,
                record
            );

        entity.point.outlineWidth =
            priority === "critical"
                ? 3
                : priority === "high"
                    ? 2
                    : 1;

        entity.label.text =
            priority === "critical"
                ? "ISS"
                : (
                    priority === "high" &&
                    group === "stations"
                )
                    ? record.name
                    : "";

        entity.properties.jarvisRecord =
            JSON.stringify(
                dossierRecord(
                    group,
                    record
                )
            );
    }


    function removeMissing(seen) {
        for (
            const [key, entity]
            of entities.entries()
        ) {
            if (!seen.has(key)) {
                satelliteSource?.entities.remove(
                    entity
                );

                entities.delete(
                    key
                );
            }
        }
    }


    function render(data) {
        const seen =
            new Set();

        let totalVisible = 0;
        let highValueCount = 0;

        for (
            const group
            of Object.keys(GROUPS)
        ) {
            const records =
                visibleRecords(
                    group,
                    data?.groups?.[group]
                );

            text(
                GROUPS[group].count,
                records.length
            );

            totalVisible +=
                records.length;

            highValueCount +=
                records.filter(
                    record =>
                        isHighValue(
                            group,
                            record
                        )
                ).length;

            for (const record of records) {
                const key =
                    entityKey(
                        group,
                        record
                    );

                seen.add(key);

                let entity =
                    entities.get(key);

                if (!entity) {
                    entity =
                        createEntity(
                            group,
                            record
                        );

                    if (entity) {
                        entities.set(
                            key,
                            entity
                        );
                    }

                    continue;
                }

                updateEntity(
                    entity,
                    group,
                    record
                );
            }
        }

        removeMissing(seen);

        text(
            "satelliteTotalCount",
            totalVisible
        );

        text(
            "satHighValueCount",
            highValueCount
        );

        text(
            "satelliteStatus",
            `CelesTrak • ${data?.generated_at || "UNKNOWN"}`
        );
    }



    function clearSelectedOrbit() {
        if (
            selectedTrackEntity &&
            satelliteSource
        ) {
            satelliteSource.entities.remove(
                selectedTrackEntity
            );
        }

        selectedTrackEntity = null;
        selectedTrackNorad = null;
    }


    async function showSelectedOrbit(record) {
        selectedSatelliteRecord =
            record;

        refreshSelectedPass(
            record
        );

        const norad =
            Number(record?.norad_id);

        if (!Number.isFinite(norad)) {
            clearSelectedOrbit();
            return;
        }

        if (
            selectedTrackNorad === norad &&
            selectedTrackEntity
        ) {
            return;
        }

        clearSelectedOrbit();

        try {
            const response =
                await fetch(
                    `/operations/space/satellites/${norad}/track`,
                    {
                        cache: "no-store",
                        headers: {
                            Accept: "application/json"
                        }
                    }
                );

            if (!response.ok) {
                throw new Error(
                    `HTTP ${response.status}`
                );
            }

            const data =
                await response.json();

            const points =
                Array.isArray(data?.points)
                    ? data.points
                    : [];

            if (points.length < 2) {
                return;
            }

            const positions = [];

            for (const point of points) {
                const lon =
                    Number(point.longitude);

                const lat =
                    Number(point.latitude);

                const alt =
                    Number(point.altitude_km);

                if (
                    !Number.isFinite(lon) ||
                    !Number.isFinite(lat) ||
                    !Number.isFinite(alt)
                ) {
                    continue;
                }

                positions.push(
                    Cesium.Cartesian3.fromDegrees(
                        lon,
                        lat,
                        alt * 1000
                    )
                );
            }

            if (positions.length < 2) {
                return;
            }

            selectedTrackEntity =
                satelliteSource.entities.add({
                    name:
                        `${data.name} orbit track`,

                    polyline: {
                        positions,

                        width:
                            record?.priority === "critical"
                                ? 3.0
                                : record?.priority === "high"
                                    ? 2.2
                                    : 1.5,

                        material:
                            record?.priority === "critical"
                                ? Cesium.Color
                                    .fromCssColorString(
                                        "#ffd34d"
                                    )
                                    .withAlpha(0.9)
                                : record?.priority === "high"
                                    ? Cesium.Color
                                        .fromCssColorString(
                                            "#ba78ff"
                                        )
                                        .withAlpha(0.85)
                                    : Cesium.Color
                                        .CYAN
                                        .withAlpha(0.75)
                    },

                    properties: {
                        jarvisGroup:
                            "satellite_track"
                    }
                });

            selectedTrackNorad = norad;

        } catch (error) {
            console.error(
                "Satellite orbit track failed:",
                error
            );
        }
    }


    function applyVisibility() {
        for (
            const [group, config]
            of Object.entries(GROUPS)
        ) {
            const groupEnabled =
                enabled(group);

            geo()?.setLayer(
                config.state,
                groupEnabled
            );

            for (
                const [key, entity]
                of entities.entries()
            ) {
                if (
                    !key.startsWith(
                        `${group}:`
                    )
                ) {
                    continue;
                }

                let record = null;

                try {
                    const raw =
                        entity.properties
                            .jarvisRecord
                            ?.getValue?.();

                    record =
                        typeof raw === "string"
                            ? JSON.parse(raw)
                            : raw;

                } catch {
                    record = null;
                }

                entity.show =
                    groupEnabled &&
                    (
                        !highValueOnlyEnabled() ||
                        (
                            record &&
                            (
                                record.priority === "critical" ||
                                record.priority === "high"
                            )
                        )
                    );
            }
        }
    }


    async function refresh() {
        try {
            /*
             * Defensive recovery: if a future Global 3D operation ever
             * removes this data source, recreate the satellite layer.
             */
            if (
                satelliteSource &&
                !viewer.dataSources.contains(
                    satelliteSource
                )
            ) {
                entities.clear();

                satelliteSource =
                    new Cesium.CustomDataSource(
                        "jarvis-space-satellites"
                    );

                viewer.dataSources.add(
                    satelliteSource
                );
            }

            const response =
                await fetch(
                    ENDPOINT,
                    {
                        cache: "no-store",
                        headers: {
                            Accept:
                                "application/json"
                        }
                    }
                );

            if (!response.ok) {
                throw new Error(
                    `HTTP ${response.status}`
                );
            }

            render(
                await response.json()
            );

        } catch (error) {
            console.error(
                "Satellite refresh failed:",
                error
            );

            text(
                "satelliteStatus",
                `SAT DATA ERROR • ${error.message}`
            );

            /*
             * Keep the last known positions visible on a
             * transient data failure.
             */
        }
    }


    function restoreLayerState() {
        const layers =
            geo()?.get()?.layers || {};

        for (
            const [group, config]
            of Object.entries(GROUPS)
        ) {
            const checkbox =
                el(config.checkbox);

            if (
                checkbox &&
                config.state in layers
            ) {
                checkbox.checked =
                    layers[config.state]
                    !== false;
            }

            checkbox?.addEventListener(
                "change",
                applyVisibility
            );
        }
    }


    function mount(targetViewer) {
        if (mounted) {
            return;
        }

        mounted = true;
        viewer = targetViewer;

        document
            .getElementById(
                "satHighValueOnly"
            )
            ?.addEventListener(
                "change",
                applyVisibility
            );


        satelliteSource =
            new Cesium.CustomDataSource(
                "jarvis-space-satellites"
            );

        viewer.dataSources.add(
            satelliteSource
        );

        restoreLayerState();

        refresh();

        timer =
            window.setInterval(
                refresh,
                REFRESH_MS
            );
    }


    window.JarvisSatelliteTracking =
        Object.freeze({
            mount,
            refresh,
            showSelectedOrbit,
            clearSelectedOrbit,
            refreshObserverSummary,
            requestBrowserLocation
        });
})();
