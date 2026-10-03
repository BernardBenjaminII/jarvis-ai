(() => {
    "use strict";

    const STATUS_URL = "/api/rf/status";
    const TASKS_URL = "/api/rf/tasks";
    const START_URL = "/api/rf/task/start";
    const STOP_URL = "/api/rf/task/stop";

    const REFRESH_MS = 2000;

    let lastSpectrum = null;

    function el(id) {
        return document.getElementById(id);
    }

    function text(id, value) {
        const node = el(id);

        if (node) {
            node.textContent = value;
        }
    }

    function hzFromMHz(value) {
        const mhz = Number(value);

        if (!Number.isFinite(mhz)) {
            return null;
        }

        return Math.round(
            mhz * 1_000_000
        );
    }

    function mhz(value) {
        const hz = Number(value);

        if (!Number.isFinite(hz)) {
            return "—";
        }

        return (
            hz / 1_000_000
        ).toFixed(3);
    }

    function taskDefaults(task) {
        if (task === "adsb") {
            el("rfFrequency").value =
                "1090.000";
        }

        if (task === "fm") {
            el("rfFrequency").value =
                "100.000";
        }

        if (task === "am") {
            el("rfFrequency").value =
                "0.999";
        }

        if (task === "manual") {
            el("rfFrequency").value =
                "100.000";
        }

        if (task === "rf_scan") {
            el("rfScanStart").value =
                "88";

            el("rfScanStop").value =
                "108";
        }

        updateControlVisibility();
    }

    function updateControlVisibility() {
        const task =
            el("rfTask")?.value;

        const scan =
            el("rfScanControls");

        const frequency =
            el("rfFrequency")
                ?.closest(".rf-control");

        if (scan) {
            scan.style.display =
                task === "rf_scan"
                    ? "block"
                    : "none";
        }

        /*
         * A sweep has a range rather than one tuned
         * frequency. Hide the single-frequency field.
         */

        if (frequency) {
            frequency.style.display =
                (
                    task === "rf_scan"
                    || task === "fm"
                    || task === "am"
                )
                    ? "none"
                    : "grid";
        }
    }

    async function request(
        url,
        options = {}
    ) {
        const response =
            await fetch(
                url,
                {
                    cache: "no-store",
                    ...options,
                }
            );

        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }

        return response.json();
    }

    function parseRtlPowerLine(line) {
        if (
            typeof line !== "string"
            || !line.includes(",")
        ) {
            return null;
        }

        const parts =
            line.split(",")
                .map(
                    value => value.trim()
                );

        if (parts.length < 7) {
            return null;
        }

        const start =
            Number(parts[2]);

        const stop =
            Number(parts[3]);

        const step =
            Number(parts[4]);

        const powers =
            parts.slice(6)
                .map(Number)
                .filter(Number.isFinite);

        if (
            !Number.isFinite(start)
            || !Number.isFinite(stop)
            || !Number.isFinite(step)
            || step <= 0
            || powers.length === 0
        ) {
            return null;
        }

        return {
            stamp:
                `${parts[0]} ${parts[1]}`,
            start,
            stop,
            step,
            powers,
        };
    }

    function latestSpectrumFromOutput(
        output
    ) {
        const rows =
            output
                .map(parseRtlPowerLine)
                .filter(Boolean);

        if (!rows.length) {
            return null;
        }

        const latestStamp =
            rows[rows.length - 1].stamp;

        const latestRows =
            rows.filter(
                row =>
                    row.stamp === latestStamp
            );

        const frequencies =
            new Map();

        latestRows.forEach(row => {
            row.powers.forEach(
                (power, index) => {
                    const frequency =
                        row.start
                        + index * row.step;

                    /*
                     * rtl_power may overlap hop edges.
                     * Keep the strongest measurement.
                     */

                    const key =
                        Math.round(frequency);

                    const existing =
                        frequencies.get(key);

                    if (
                        existing === undefined
                        || power > existing
                    ) {
                        frequencies.set(
                            key,
                            power
                        );
                    }
                }
            );
        });

        const points =
            Array.from(
                frequencies.entries()
            )
                .map(
                    ([frequency, power]) => ({
                        frequency,
                        power,
                    })
                )
                .sort(
                    (a, b) =>
                        a.frequency
                        - b.frequency
                );

        if (points.length < 2) {
            return null;
        }

        const powers =
            points.map(
                point => point.power
            );

        const minimum =
            Math.min(...powers);

        const maximum =
            Math.max(...powers);

        const start =
            points[0].frequency;

        const stop =
            points[
                points.length - 1
            ].frequency;

        const step =
            latestRows[0].step;

        return {
            stamp: latestStamp,
            start,
            stop,
            step,
            minimum,
            maximum,
            points,
            peaks:
                findPeaks(
                    points,
                    step
                ),
        };
    }

    function findPeaks(
        points,
        step
    ) {
        if (points.length < 3) {
            return [];
        }

        const candidates = [];

        for (
            let index = 1;
            index < points.length - 1;
            index += 1
        ) {
            const previous =
                points[index - 1];

            const current =
                points[index];

            const next =
                points[index + 1];

            if (
                current.power >= previous.power
                && current.power >= next.power
            ) {
                candidates.push(current);
            }
        }

        candidates.sort(
            (a, b) =>
                b.power - a.power
        );

        const span =
            points[
                points.length - 1
            ].frequency
            - points[0].frequency;

        /*
         * Avoid reporting several adjacent FFT bins
         * as separate "signals".
         */

        const separation =
            Math.max(
                step * 5,
                span / 100
            );

        const selected = [];

        for (const candidate of candidates) {
            const separated =
                selected.every(
                    peak =>
                        Math.abs(
                            peak.frequency
                            - candidate.frequency
                        ) >= separation
                );

            if (separated) {
                selected.push(candidate);
            }

            if (selected.length >= 5) {
                break;
            }
        }

        return selected;
    }

    function drawSpectrum(spectrum) {
        const canvas =
            el("rfSpectrumCanvas");

        if (!canvas || !spectrum) {
            return;
        }

        const panel =
            el("rfSpectrumPanel");

        if (panel) {
            panel.hidden = false;
        }

        const cssWidth =
            Math.max(
                280,
                Math.floor(
                    canvas.clientWidth
                    || 500
                )
            );

        const cssHeight =
            Math.max(
                150,
                Math.floor(
                    canvas.clientHeight
                    || 180
                )
            );

        const ratio =
            Math.max(
                1,
                window.devicePixelRatio
                || 1
            );

        canvas.width =
            Math.floor(
                cssWidth * ratio
            );

        canvas.height =
            Math.floor(
                cssHeight * ratio
            );

        const ctx =
            canvas.getContext("2d");

        if (!ctx) {
            return;
        }

        ctx.setTransform(
            ratio,
            0,
            0,
            ratio,
            0,
            0
        );

        ctx.clearRect(
            0,
            0,
            cssWidth,
            cssHeight
        );

        const left = 42;
        const right = 10;
        const top = 10;
        const bottom = 25;

        const width =
            cssWidth - left - right;

        const height =
            cssHeight - top - bottom;

        /*
         * Grid.
         */

        ctx.lineWidth = 1;
        ctx.strokeStyle =
            "rgba(120,230,200,.12)";

        for (
            let index = 0;
            index <= 4;
            index += 1
        ) {
            const y =
                top
                + height
                * index / 4;

            ctx.beginPath();
            ctx.moveTo(left, y);
            ctx.lineTo(
                left + width,
                y
            );
            ctx.stroke();
        }

        for (
            let index = 0;
            index <= 4;
            index += 1
        ) {
            const x =
                left
                + width
                * index / 4;

            ctx.beginPath();
            ctx.moveTo(x, top);
            ctx.lineTo(
                x,
                top + height
            );
            ctx.stroke();
        }

        const range =
            Math.max(
                1,
                spectrum.maximum
                - spectrum.minimum
            );

        const floor =
            spectrum.minimum
            - range * 0.08;

        const ceiling =
            spectrum.maximum
            + range * 0.08;

        const powerRange =
            Math.max(
                1,
                ceiling - floor
            );

        const frequencyRange =
            Math.max(
                1,
                spectrum.stop
                - spectrum.start
            );

        /*
         * Spectrum trace.
         */

        ctx.lineWidth = 1.5;
        ctx.strokeStyle =
            "rgba(120,230,200,.92)";

        ctx.beginPath();

        spectrum.points.forEach(
            (point, index) => {
                const x =
                    left
                    + (
                        point.frequency
                        - spectrum.start
                    )
                    / frequencyRange
                    * width;

                const y =
                    top
                    + (
                        ceiling
                        - point.power
                    )
                    / powerRange
                    * height;

                if (index === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            }
        );

        ctx.stroke();

        /*
         * Axis labels.
         */

        ctx.fillStyle =
            "rgba(210,240,232,.72)";

        ctx.font =
            "10px monospace";

        ctx.textAlign = "left";

        ctx.fillText(
            `${spectrum.maximum.toFixed(1)}`,
            2,
            top + 8
        );

        ctx.fillText(
            `${spectrum.minimum.toFixed(1)}`,
            2,
            top + height
        );

        ctx.textAlign = "left";

        ctx.fillText(
            `${mhz(spectrum.start)}`,
            left,
            cssHeight - 7
        );

        ctx.textAlign = "center";

        ctx.fillText(
            `${mhz(
                spectrum.start
                + frequencyRange / 2
            )} MHz`,
            left + width / 2,
            cssHeight - 7
        );

        ctx.textAlign = "right";

        ctx.fillText(
            `${mhz(spectrum.stop)}`,
            left + width,
            cssHeight - 7
        );
    }

    function renderSpectrum(spectrum) {
        const panel =
            el("rfSpectrumPanel");

        if (!spectrum) {
            if (panel) {
                panel.hidden = true;
            }

            lastSpectrum = null;

            return;
        }

        lastSpectrum = spectrum;

        if (panel) {
            panel.hidden = false;
        }

        text(
            "rfSpectrumMeta",
            `${mhz(spectrum.start)}–`
            + `${mhz(spectrum.stop)} MHz`
            + ` · ${spectrum.points.length} bins`
            + ` · ${(spectrum.step / 1000).toFixed(1)} kHz/bin`
        );

        if (spectrum.peaks.length) {
            text(
                "rfSpectrumPeaks",
                "PEAKS  "
                + spectrum.peaks
                    .map(
                        peak =>
                            `${mhz(
                                peak.frequency
                            )} MHz `
                            + `${peak.power.toFixed(1)}`
                    )
                    .join("   •   ")
            );
        } else {
            text(
                "rfSpectrumPeaks",
                "No distinct peaks detected."
            );
        }

        drawSpectrum(spectrum);

        window.dispatchEvent(
            new CustomEvent(
                "jarvis:rf-spectrum",
                {
                    detail: spectrum,
                }
            )
        );
    }

    function scanSummary(spectrum) {
        if (!spectrum) {
            return "Waiting for spectrum data...";
        }

        const strongest =
            spectrum.peaks[0];

        const lines = [
            `Sweep: ${mhz(spectrum.start)}–${mhz(spectrum.stop)} MHz`,
            `Resolution: ${(spectrum.step / 1000).toFixed(2)} kHz`,
            `Bins: ${spectrum.points.length}`,
            `Power range: ${spectrum.minimum.toFixed(1)} to ${spectrum.maximum.toFixed(1)}`,
        ];

        if (strongest) {
            lines.push(
                `Strongest peak: ${mhz(
                    strongest.frequency
                )} MHz  ${strongest.power.toFixed(1)}`
            );
        }

        lines.push(
            `Updated: ${spectrum.stamp}`
        );

        return lines.join("\n");
    }

    function render(status) {
        text(
            "rfState",
            String(
                status.state
                || "unknown"
            ).toUpperCase()
        );

        text(
            "rfDetail",
            status.detail
            || "No RF task active."
        );

        window.dispatchEvent(
            new CustomEvent(
                "jarvis:rf-status",
                {
                    detail: status,
                }
            )
        );

        const output =
            Array.isArray(
                status.output_tail
            )
                ? status.output_tail
                : [];

        const spectrum =
            latestSpectrumFromOutput(
                output
            );

        if (spectrum) {
            renderSpectrum(spectrum);

            text(
                "rfOutput",
                scanSummary(spectrum)
            );

            return;
        }

        renderSpectrum(null);

        /*
         * ADS-B / manual task output remains textual.
         */

        text(
            "rfOutput",
            output
                .slice(-10)
                .join("\n")
        );
    }

    async function refresh() {
        try {
            const status =
                await request(
                    STATUS_URL
                );

            render(status);

        } catch (error) {
            text(
                "rfState",
                "ERROR"
            );

            text(
                "rfDetail",
                error.message
            );
        }
    }

    function buildRequest() {
        const task =
            el("rfTask").value;

        const body = {
            task,
            gain:
                el("rfGain").value
                || "auto",
        };

        /*
         * A spectrum sweep has no single tuned frequency.
         */

        if (task !== "rf_scan") {
            const frequency =
                hzFromMHz(
                    el("rfFrequency").value
                );

            if (frequency !== null) {
                body.frequency_hz =
                    frequency;
            }
        }

        if (task === "rf_scan") {
            body.scan_start_hz =
                hzFromMHz(
                    el("rfScanStart").value
                );

            body.scan_stop_hz =
                hzFromMHz(
                    el("rfScanStop").value
                );
        }

        return body;
    }

    async function startTask() {
        text(
            "rfDetail",
            "Starting task..."
        );

        try {
            const status =
                await request(
                    START_URL,
                    {
                        method: "POST",
                        headers: {
                            "Content-Type":
                                "application/json",
                        },
                        body:
                            JSON.stringify(
                                buildRequest()
                            ),
                    }
                );

            render(status);

        } catch (error) {
            text(
                "rfState",
                "ERROR"
            );

            text(
                "rfDetail",
                error.message
            );
        }
    }

    async function stopTask() {
        try {
            const status =
                await request(
                    STOP_URL,
                    {
                        method: "POST",
                    }
                );

            render(status);

        } catch (error) {
            text(
                "rfState",
                "ERROR"
            );

            text(
                "rfDetail",
                error.message
            );
        }
    }

    async function loadTasks() {
        try {
            const tasks =
                await request(
                    TASKS_URL
                );

            const unavailable =
                tasks.filter(
                    item =>
                        !item.available
                );

            if (unavailable.length) {
                console.warn(
                    "Unavailable RF tasks:",
                    unavailable
                );
            }

        } catch (error) {
            console.warn(
                "RF task inventory failed:",
                error
            );
        }
    }

    function mount() {
        if (!el("rfSwitchboard")) {
            return;
        }

        el("rfTask")
            ?.addEventListener(
                "change",
                event => {
                    taskDefaults(
                        event.target.value
                    );
                }
            );

        el("rfStart")
            ?.addEventListener(
                "click",
                startTask
            );

        el("rfStop")
            ?.addEventListener(
                "click",
                stopTask
            );

        window.addEventListener(
            "resize",
            () => {
                if (lastSpectrum) {
                    drawSpectrum(
                        lastSpectrum
                    );
                }
            }
        );

        updateControlVisibility();
        loadTasks();
        refresh();

        window.setInterval(
            () => {
                if (!document.hidden) {
                    refresh();
                }
            },
            REFRESH_MS
        );
    }

    window.JarvisRF = {
        refresh,
        startTask,
        stopTask,
    };

    if (
        document.readyState
        === "loading"
    ) {
        document.addEventListener(
            "DOMContentLoaded",
            mount,
            { once: true }
        );
    } else {
        mount();
    }
})();
