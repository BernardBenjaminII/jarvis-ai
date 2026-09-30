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


    function satelliteColor(group) {
        if (group === "stations") {
            return Cesium.Color.WHITE;
        }

        if (group === "gps") {
            return Cesium.Color.fromCssColorString(
                "#61d9ff"
            );
        }

        return Cesium.Color.fromCssColorString(
            "#77ef9e"
        );
    }


    function satelliteSize(group) {
        if (group === "stations") {
            return 9;
        }

        if (group === "gps") {
            return 6;
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
            satelliteColor(group);

        if (!satelliteSource) {
            return null;
        }

        const entity =
            satelliteSource.entities.add({
                name: record.name,

                position: pos,

                point: {
                    pixelSize:
                        satelliteSize(group),

                    color,

                    outlineColor:
                        Cesium.Color.BLACK,

                    outlineWidth: 1,

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
                        group === "stations"
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

                show: enabled(group)
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

        entity.show =
            enabled(group);

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
                        width: 1.5,

                        material:
                            Cesium.Color
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
            const value =
                enabled(group);

            geo()?.setLayer(
                config.state,
                value
            );

            for (
                const [key, entity]
                of entities.entries()
            ) {
                if (
                    key.startsWith(
                        `${group}:`
                    )
                ) {
                    entity.show =
                        value;
                }
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
            clearSelectedOrbit
        });
})();
