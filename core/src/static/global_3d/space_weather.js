(() => {
    "use strict";

    const WEATHER_ENDPOINT =
        "/operations/space/weather";

    const AURORA_ENDPOINT =
        "/operations/space/weather/aurora";

    const REFRESH_MS = 180000;

    let viewer = null;
    let auroraLayer = null;
    let mounted = false;
    let lastWeather = null;

    function geo() {
        return window.JARVIS_GEOSPATIAL;
    }

    function el(id) {
        return document.getElementById(id);
    }

    function number(value) {
        const n = Number(value);
        return Number.isFinite(n) ? n : null;
    }

    function text(id, value) {
        const node = el(id);
        if (node) node.textContent = value;
    }

    function layerEnabled() {
        const checkbox = el("layerSpaceWeather");

        return checkbox
            ? checkbox.checked
            : true;
    }

    function setStatus(value) {
        text("spaceWeatherState", value);
    }

    function kpState(kp) {
        if (kp === null) return "---";

        if (kp >= 9) return "G5";
        if (kp >= 8) return "G4";
        if (kp >= 7) return "G3";
        if (kp >= 6) return "G2";
        if (kp >= 5) return "G1";

        return "QUIET";
    }

    function scaleValue(scales, key) {
        if (!scales || typeof scales !== "object") {
            return "-";
        }

        /*
         * NOAA scales payloads have changed shape over time.
         * Walk likely containers instead of binding this UI to
         * one exact upstream representation.
         */
        const candidates = [
            scales[key],
            scales[key?.toLowerCase?.()],
            scales[0]?.[key],
            scales[0]?.[key?.toLowerCase?.()],
        ];

        for (const item of candidates) {
            if (item === undefined || item === null) {
                continue;
            }

            if (
                typeof item === "string" ||
                typeof item === "number"
            ) {
                return String(item);
            }

            if (typeof item === "object") {
                for (const field of [
                    "Scale",
                    "scale",
                    "Current",
                    "current",
                    "value"
                ]) {
                    if (item[field] !== undefined) {
                        return String(item[field]);
                    }
                }
            }
        }

        return "-";
    }

    function solarWindValue(raw, field) {
        if (!raw || typeof raw !== "object") {
            return null;
        }

        return number(raw[field]);
    }

    function renderWeather(data) {
        lastWeather = data;

        const kp = number(data?.kp_current);

        text(
            "spaceKp",
            kp === null
                ? "---"
                : kp.toFixed(2)
        );

        const wind =
            solarWindValue(
                data?.solar_wind,
                "speed_km_s"
            );

        text(
            "spaceWind",
            wind === null
                ? "---"
                : `${Math.round(wind)} km/s`
        );

        const mag =
            solarWindValue(
                data?.solar_wind,
                "magnetic_field_nt"
            );

        text(
            "spaceMag",
            mag === null
                ? "---"
                : `${mag.toFixed(1)} nT`
        );

        text(
            "spaceAlerts",
            Array.isArray(data?.alerts)
                ? data.alerts.length
                : 0
        );

        const scales = data?.scales || {};

        text(
            "spaceScales",
            [
                `G${scaleValue(scales, "G")}`,
                `R${scaleValue(scales, "R")}`,
                `S${scaleValue(scales, "S")}`
            ].join(" / ")
        );

        const sources =
            Array.isArray(data?.sources)
                ? data.sources
                : [];

        const good =
            sources.filter(source => source?.ok).length;

        text(
            "spaceSourceState",
            `NOAA SWPC ${good}/${sources.length} • ` +
            `${data?.generated_at || "UNKNOWN"}`
        );

        setStatus(kpState(kp));
    }


    function removeAuroraLayer() {
        if (!viewer || !auroraLayer) {
            return;
        }

        try {
            viewer.imageryLayers.remove(
                auroraLayer,
                true
            );
        } catch (error) {
            console.warn(
                "Space aurora layer removal failed:",
                error
            );
        }

        auroraLayer = null;
    }


    function probabilityColor(probability) {
        /*
         * OVATION values are probabilities, not generic
         * 0..100 heat-map intensities.
         *
         * Quiet conditions can have a global maximum around
         * only 10-15%. Suppress the low-value background and
         * stretch the operationally useful range visually.
         */

        const p =
            Math.max(
                0,
                Math.min(
                    100,
                    number(probability) || 0
                )
            );

        if (p < 5) {
            return [0, 0, 0, 0];
        }

        if (p < 7) {
            return [40, 190, 125, 70];
        }

        if (p < 9) {
            return [60, 225, 145, 110];
        }

        if (p < 11) {
            return [180, 235, 120, 155];
        }

        if (p < 15) {
            return [255, 190, 90, 200];
        }

        if (p < 30) {
            return [255, 105, 80, 220];
        }

        return [255, 55, 55, 235];
    }


    function buildAuroraCanvas(coordinates) {
        /*
         * NOAA OVATION is a global lon/lat/probability grid.
         *
         * Instead of creating ~65,000 Cesium entities, rasterize
         * it once into an equirectangular texture. Cesium then
         * handles it as ONE imagery layer.
         */

        const WIDTH = 720;
        const HEIGHT = 360;

        const canvas =
            document.createElement("canvas");

        canvas.width = WIDTH;
        canvas.height = HEIGHT;

        const ctx =
            canvas.getContext(
                "2d",
                { alpha: true }
            );

        const image =
            ctx.createImageData(
                WIDTH,
                HEIGHT
            );

        function paint(x, y, rgba) {
            if (
                x < 0 ||
                y < 0 ||
                x >= WIDTH ||
                y >= HEIGHT
            ) {
                return;
            }

            const offset =
                (y * WIDTH + x) * 4;

            /*
             * Keep whichever point has the strongest alpha,
             * avoiding unnecessary blending work.
             */
            if (
                rgba[3] <=
                image.data[offset + 3]
            ) {
                return;
            }

            image.data[offset] = rgba[0];
            image.data[offset + 1] = rgba[1];
            image.data[offset + 2] = rgba[2];
            image.data[offset + 3] = rgba[3];
        }

        for (const coordinate of coordinates) {
            if (
                !Array.isArray(coordinate) ||
                coordinate.length < 3
            ) {
                continue;
            }

            let lon = number(coordinate[0]);
            const lat = number(coordinate[1]);
            const probability =
                number(coordinate[2]);

            if (
                lon === null ||
                lat === null ||
                probability === null
            ) {
                continue;
            }

            /*
             * NOAA commonly expresses longitude 0..360.
             */
            if (lon > 180) {
                lon -= 360;
            }

            if (
                lon < -180 ||
                lon > 180 ||
                lat < -90 ||
                lat > 90
            ) {
                continue;
            }

            const x =
                Math.floor(
                    ((lon + 180) / 360) *
                    (WIDTH - 1)
                );

            const y =
                Math.floor(
                    ((90 - lat) / 180) *
                    (HEIGHT - 1)
                );

            const rgba =
                probabilityColor(probability);

            /*
             * Slight 2x2 footprint removes gaps between
             * source-grid samples without generating entities.
             */
            paint(x, y, rgba);
            paint(x + 1, y, rgba);
            paint(x, y + 1, rgba);
            paint(x + 1, y + 1, rgba);
        }

        ctx.putImageData(image, 0, 0);

        return canvas;
    }


    function renderAurora(data) {
        if (!viewer) return;

        const coordinates =
            data?.aurora?.coordinates;

        if (Array.isArray(coordinates)) {
            const probabilities =
                coordinates
                    .map(row =>
                        Array.isArray(row)
                            ? number(row[2])
                            : null
                    )
                    .filter(value =>
                        value !== null
                    );

            if (probabilities.length) {
                const maxProbability =
                    Math.max(...probabilities);

                let state = "LOW";

                if (maxProbability >= 50) {
                    state = "EXTREME";
                } else if (maxProbability >= 30) {
                    state = "HIGH";
                } else if (maxProbability >= 15) {
                    state = "MODERATE";
                }

                text(
                    "spaceAurora",
                    `${state} ${maxProbability.toFixed(0)}%`
                );
            } else {
                text("spaceAurora", "---");
            }
        }

        removeAuroraLayer();

        if (
            !layerEnabled() ||
            !Array.isArray(coordinates) ||
            !coordinates.length
        ) {
            return;
        }

        const canvas =
            buildAuroraCanvas(coordinates);

        const provider =
            new Cesium.SingleTileImageryProvider({
                url: canvas.toDataURL("image/png"),
                rectangle:
                    Cesium.Rectangle.fromDegrees(
                        -180,
                        -90,
                        180,
                        90
                    )
            });

        auroraLayer =
            viewer.imageryLayers.addImageryProvider(
                provider
            );

        auroraLayer.alpha = 0.68;
        auroraLayer.show = layerEnabled();
    }


    async function fetchJson(url) {
        const response =
            await fetch(
                url,
                {
                    cache: "no-store",
                    headers: {
                        Accept: "application/json"
                    }
                }
            );

        if (!response.ok) {
            throw new Error(
                `${url}: HTTP ${response.status}`
            );
        }

        return response.json();
    }


    async function refresh() {
        try {
            const weather =
                await fetchJson(
                    WEATHER_ENDPOINT
                );

            renderWeather(weather);

            if (layerEnabled()) {
                const aurora =
                    await fetchJson(
                        AURORA_ENDPOINT
                    );

                renderAurora(aurora);
            } else {
                removeAuroraLayer();
            }

        } catch (error) {
            console.error(
                "Jarvis space weather refresh failed:",
                error
            );

            setStatus("ERROR");

            text(
                "spaceSourceState",
                `SPACE DATA ERROR • ${error.message}`
            );

            /*
             * Leave last-known-good aurora visible unless
             * the operator explicitly disables the layer.
             */
        }
    }


    function syncLayerState() {
        const enabled = layerEnabled();

        geo()?.setLayer(
            "space_weather",
            enabled
        );

        if (auroraLayer) {
            auroraLayer.show = enabled;
        }

        if (enabled) {
            refresh();
        } else {
            removeAuroraLayer();
        }
    }


    function mount(targetViewer) {
        if (mounted) {
            return;
        }

        mounted = true;
        viewer = targetViewer;

        const checkbox =
            el("layerSpaceWeather");

        const shared =
            geo()?.get()?.layers || {};

        if (
            checkbox &&
            "space_weather" in shared
        ) {
            checkbox.checked =
                shared.space_weather !== false;
        }

        checkbox?.addEventListener(
            "change",
            syncLayerState
        );

        refresh();

        window.setInterval(
            refresh,
            REFRESH_MS
        );
    }


    window.JarvisSpaceWeather =
        Object.freeze({
            mount,
            refresh
        });
})();
