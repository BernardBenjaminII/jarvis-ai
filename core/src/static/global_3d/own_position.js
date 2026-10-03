(() => {
    "use strict";

    // JARVIS_OWN_POSITION_R1

    const REFRESH_MS = 5000;
    const API = "/api/sensors/mobile/status";

    let viewer = null;
    let source = null;
    let entity = null;
    let latest = null;

    let layerCheckbox = null;
    let statusElement = null;
    let flyButton = null;


    function validCoordinates(data) {
        const latitude = Number(data?.latitude);
        const longitude = Number(data?.longitude);

        return (
            Number.isFinite(latitude) &&
            Number.isFinite(longitude) &&
            latitude >= -90 &&
            latitude <= 90 &&
            longitude >= -180 &&
            longitude <= 180
        );
    }


    function finite(value, fallback = null) {
        const number = Number(value);

        return Number.isFinite(number)
            ? number
            : fallback;
    }


    function statusFor(data) {
        if (data?.state === "online") {
            if (data?.fix_stale === true) {
                return "STALE FIX";
            }

            return "LIVE";
        }

        return "OFFLINE";
    }


    function colorFor(status) {
        if (status === "LIVE") {
            return Cesium.Color.fromCssColorString("#45f3ff");
        }

        if (status === "STALE FIX") {
            return Cesium.Color.fromCssColorString("#f0b84b");
        }

        return Cesium.Color.fromCssColorString("#8c949c");
    }


    function formatCoordinate(value) {
        const number = finite(value);

        return number === null
            ? "—"
            : number.toFixed(6);
    }


    function formatMeters(value) {
        const number = finite(value);

        return number === null
            ? "—"
            : `${number.toFixed(1)} m`;
    }


    function formatAge(value) {
        const number = finite(value);

        return number === null
            ? "—"
            : `${number.toFixed(0)} s`;
    }


    function createUi() {
        const layersSection =
            document.querySelector("#leftPanel section");

        if (!layersSection) {
            console.warn(
                "[own-position] Global 3D layers panel not found."
            );
            return;
        }

        if (document.getElementById("layerOwnPosition")) {
            layerCheckbox =
                document.getElementById("layerOwnPosition");

            statusElement =
                document.getElementById("ownPositionStatus");

            flyButton =
                document.getElementById("ownPositionFly");

            return;
        }

        const row = document.createElement("label");
        row.className = "layer-row own-position-row";

        row.innerHTML = `
            <input
                id="layerOwnPosition"
                type="checkbox"
                checked>

            <span
                class="legend"
                style="
                    background:#45f3ff;
                    border:1px solid rgba(255,255,255,.7);
                    border-radius:50%;
                ">
            </span>

            My Position

            <strong id="ownPositionState">
                ---
            </strong>
        `;

        const status = document.createElement("div");
        status.id = "ownPositionStatus";
        status.className = "satellite-observer-status";
        status.textContent = "Waiting for mobile GNSS";

        const button = document.createElement("button");
        button.id = "ownPositionFly";
        button.type = "button";
        button.className = "satellite-location-button";
        button.textContent = "FLY TO ME";

        const firstSpaceRow =
            document.getElementById("layerSpaceWeather")
                ?.closest("label");

        if (firstSpaceRow) {
            layersSection.insertBefore(row, firstSpaceRow);
            layersSection.insertBefore(status, firstSpaceRow);
            layersSection.insertBefore(button, firstSpaceRow);
        } else {
            layersSection.appendChild(row);
            layersSection.appendChild(status);
            layersSection.appendChild(button);
        }

        layerCheckbox =
            document.getElementById("layerOwnPosition");

        statusElement =
            document.getElementById("ownPositionStatus");

        flyButton =
            document.getElementById("ownPositionFly");

        layerCheckbox?.addEventListener(
            "change",
            () => {
                if (source) {
                    source.show =
                        layerCheckbox.checked;
                }
            }
        );

        flyButton?.addEventListener(
            "click",
            flyToOwnPosition
        );
    }


    function createSource() {
        source =
            new Cesium.CustomDataSource(
                "JARVIS Own Position"
            );

        viewer.dataSources.add(source);
    }


    function createEntity() {
        entity = source.entities.add({
            id: "jarvis-own-position",

            show: false,

            point: {
                pixelSize: 15,
                color:
                    Cesium.Color.fromCssColorString(
                        "#45f3ff"
                    ),
                outlineColor: Cesium.Color.BLACK,
                outlineWidth: 3,

                scaleByDistance:
                    new Cesium.NearFarScalar(
                        1000,
                        1.35,
                        20000000,
                        0.75
                    ),

                disableDepthTestDistance:
                    Number.POSITIVE_INFINITY
            },

            ellipse: {
                semiMajorAxis: 5,
                semiMinorAxis: 5,

                material:
                    Cesium.Color
                        .fromCssColorString("#45f3ff")
                        .withAlpha(0.12),

                outline: true,

                outlineColor:
                    Cesium.Color
                        .fromCssColorString("#45f3ff")
                        .withAlpha(0.8)
            },

            label: {
                text: "MY POSITION",

                font:
                    "600 13px sans-serif",

                fillColor:
                    Cesium.Color.WHITE,

                outlineColor:
                    Cesium.Color.BLACK,

                outlineWidth: 4,

                style:
                    Cesium.LabelStyle
                        .FILL_AND_OUTLINE,

                verticalOrigin:
                    Cesium.VerticalOrigin.BOTTOM,

                pixelOffset:
                    new Cesium.Cartesian2(
                        0,
                        -18
                    ),

                distanceDisplayCondition:
                    new Cesium.DistanceDisplayCondition(
                        0,
                        3000000
                    ),

                disableDepthTestDistance:
                    Number.POSITIVE_INFINITY
            },

            properties: {
                jarvisGroup: "own_position",
                nodeId: "iphone14promax"
            }
        });
    }


    function updateEntity(data) {
        if (!entity || !validCoordinates(data)) {
            return;
        }

        const latitude =
            Number(data.latitude);

        const longitude =
            Number(data.longitude);

        const altitude =
            Math.max(
                0,
                finite(data.altitude_m, 0)
            );

        const accuracy =
            Math.max(
                1,
                finite(
                    data.horizontal_accuracy_m,
                    5
                )
            );

        const status =
            statusFor(data);

        const color =
            colorFor(status);

        entity.position =
            Cesium.Cartesian3.fromDegrees(
                longitude,
                latitude,
                altitude + 2
            );

        entity.point.color = color;

        entity.ellipse.semiMajorAxis =
            accuracy;

        entity.ellipse.semiMinorAxis =
            accuracy;

        entity.ellipse.material =
            color.withAlpha(0.12);

        entity.ellipse.outlineColor =
            color.withAlpha(0.8);

        entity.label.text =
            status === "LIVE"
                ? "MY POSITION • LIVE"
                : `MY POSITION • ${status}`;

        entity.label.fillColor =
            color;

        entity.show = true;

        if (source) {
            source.show =
                layerCheckbox
                    ? layerCheckbox.checked
                    : true;
        }
    }


    function updateUi(data) {
        const status =
            statusFor(data);

        const state =
            document.getElementById(
                "ownPositionState"
            );

        if (state) {
            state.textContent = status;
        }

        if (!statusElement) {
            return;
        }

        if (!validCoordinates(data)) {
            statusElement.textContent =
                `${status} • no position available`;

            return;
        }

        statusElement.textContent =
            [
                status,
                data?.source || "MOBILE GNSS",
                `${formatCoordinate(data.latitude)}, ` +
                    `${formatCoordinate(data.longitude)}`,
                `ALT ${formatMeters(data.altitude_m)}`,
                `ACC ±${formatMeters(
                    data.horizontal_accuracy_m
                )}`,
                `FIX ${formatAge(
                    data.fix_age_seconds
                )}`
            ].join(" • ");
    }


    function flyToOwnPosition() {
        if (!latest || !validCoordinates(latest)) {
            return;
        }

        const latitude =
            Number(latest.latitude);

        const longitude =
            Number(latest.longitude);

        viewer.camera.flyTo({
            destination:
                Cesium.Cartesian3.fromDegrees(
                    longitude,
                    latitude,
                    75000
                ),

            duration: 1.2
        });
    }


    async function refresh() {
        try {
            const response =
                await fetch(
                    API,
                    {
                        headers: {
                            Accept: "application/json"
                        },
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

            latest = data;

            updateEntity(data);
            updateUi(data);

        } catch (error) {
            console.warn(
                "[own-position] refresh failed:",
                error
            );

            const state =
                document.getElementById(
                    "ownPositionState"
                );

            if (state) {
                state.textContent =
                    "LINK ERROR";
            }

            if (statusElement) {
                statusElement.textContent =
                    "Own-position telemetry unavailable";
            }

            /*
             * Preserve the last known marker.
             * Never manufacture a new position.
             */
            if (entity) {
                const color =
                    colorFor("OFFLINE");

                entity.point.color = color;
                entity.label.fillColor = color;
                entity.label.text =
                    "MY POSITION • LINK ERROR";
            }
        }
    }


    function init() {
        viewer =
            window.JARVIS_GLOBAL_3D_VIEWER;

        if (!viewer || !window.Cesium) {
            console.error(
                "[own-position] Cesium viewer unavailable."
            );
            return;
        }

        createUi();
        createSource();
        createEntity();

        refresh();

        window.setInterval(
            refresh,
            REFRESH_MS
        );

        window.JARVIS_OWN_POSITION = {
            refresh,
            flyToOwnPosition,
            source
        };

        console.info(
            "[own-position] R1 initialized."
        );
    }


    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            init,
            { once: true }
        );
    } else {
        init();
    }
})();
