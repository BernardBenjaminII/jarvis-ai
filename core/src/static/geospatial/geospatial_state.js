(() => {
    "use strict";

    const STORAGE_KEY = "jarvis.geospatial.state.r1";

    const DEFAULT_STATE = Object.freeze({
        layers: {
            incidents: true,
            nuclear: true,
            security: true,
            space_weather: true,
            satellites_stations: true,
            satellites_gps: true,
            satellites_weather: true
        },
        timeWindowHours: 168,
        selectedRecord: null,
        viewport: {
            latitude: 22,
            longitude: 8,
            zoom: 2,
            altitude: 18000000
        },
        updatedAt: null
    });

    function clone(value) {
        return JSON.parse(JSON.stringify(value));
    }

    function merge(base, patch) {
        const out = clone(base);

        if (!patch || typeof patch !== "object") {
            return out;
        }

        if (patch.layers && typeof patch.layers === "object") {
            Object.assign(out.layers, patch.layers);
        }

        if (patch.viewport && typeof patch.viewport === "object") {
            Object.assign(out.viewport, patch.viewport);
        }

        if ("timeWindowHours" in patch) {
            out.timeWindowHours = Number(patch.timeWindowHours) || 0;
        }

        if ("selectedRecord" in patch) {
            out.selectedRecord = patch.selectedRecord;
        }

        if ("updatedAt" in patch) {
            out.updatedAt = patch.updatedAt;
        }

        return out;
    }

    function load() {
        try {
            const raw = sessionStorage.getItem(STORAGE_KEY);

            if (!raw) {
                return clone(DEFAULT_STATE);
            }

            return merge(DEFAULT_STATE, JSON.parse(raw));
        } catch (error) {
            console.warn("JARVIS geospatial state load failed:", error);
            return clone(DEFAULT_STATE);
        }
    }

    let state = load();

    function save() {
        state.updatedAt = new Date().toISOString();

        try {
            sessionStorage.setItem(
                STORAGE_KEY,
                JSON.stringify(state)
            );
        } catch (error) {
            console.warn("JARVIS geospatial state save failed:", error);
        }

        window.dispatchEvent(
            new CustomEvent(
                "jarvis:geospatial-state",
                { detail: clone(state) }
            )
        );
    }

    function get() {
        return clone(state);
    }

    function patch(update) {
        state = merge(state, update);
        save();
        return get();
    }

    function setLayer(name, enabled) {
        if (!(name in state.layers)) {
            console.warn("Unknown geospatial layer:", name);
            return get();
        }

        state.layers[name] = Boolean(enabled);
        save();
        return get();
    }

    function setViewport(viewport) {
        state.viewport = {
            ...state.viewport,
            ...viewport
        };
        save();
        return get();
    }

    function setSelectedRecord(record) {
        state.selectedRecord = record || null;
        save();
        return get();
    }

    function setTimeWindowHours(hours) {
        state.timeWindowHours = Number(hours) || 0;
        save();
        return get();
    }

    function reset() {
        state = clone(DEFAULT_STATE);
        save();
        return get();
    }

    window.JARVIS_GEOSPATIAL = Object.freeze({
        get,
        patch,
        setLayer,
        setViewport,
        setSelectedRecord,
        setTimeWindowHours,
        reset
    });
})();
