(() => {
    "use strict";

    const AIRCRAFT_URL = "/api/rf/adsb/aircraft";
    const STATS_URL = "/api/rf/adsb/stats";
    const POLL_MS = 1000;

    let selectedIcao = null;

    function el(id) {
        return document.getElementById(id);
    }

    function esc(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function present(value) {
        return !(
            value === null ||
            value === undefined ||
            value === ""
        );
    }

    function show(value, suffix = "") {
        if (!present(value)) {
            return "—";
        }

        return `${esc(value)}${suffix}`;
    }

    function whole(value) {
        const number = Number(value);

        if (!Number.isFinite(number)) {
            return "—";
        }

        return Math.round(number).toLocaleString();
    }

    function direction(value) {
        const degrees = Number(value);

        if (!Number.isFinite(degrees)) {
            return "—";
        }

        const names = [
            "N", "NNE", "NE", "ENE",
            "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW",
            "W", "WNW", "NW", "NNW",
        ];

        const normalized =
            ((degrees % 360) + 360) % 360;

        const cardinal =
            names[Math.round(normalized / 22.5) % 16];

        return `${Math.round(normalized)}° ${cardinal}`;
    }

    function emergency(track) {
        return ["7500", "7600", "7700"]
            .includes(String(track?.squawk ?? ""));
    }

    function emergencyText(squawk) {
        switch (String(squawk ?? "")) {
            case "7500":
                return "HIJACK";
            case "7600":
                return "RADIO FAILURE";
            case "7700":
                return "EMERGENCY";
            default:
                return null;
        }
    }

    async function request(url) {
        const response = await fetch(url, {
            cache: "no-store",
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        return response.json();
    }

    function ensureUI() {
        if (el("adsbTracker")) {
            return;
        }

        const output = el("rfOutput");

        if (!output || !output.parentNode) {
            return;
        }

        const panel = document.createElement("div");

        panel.id = "adsbTracker";
        panel.className = "adsb-tracker";

        panel.innerHTML = `
            <div class="adsb-metrics">
                <div>
                    <span>TRACKS</span>
                    <strong id="adsbTrackCount">0</strong>
                </div>

                <div>
                    <span>POSITION</span>
                    <strong id="adsbPositionCount">0</strong>
                </div>

                <div>
                    <span>MSG</span>
                    <strong id="adsbMessageCount">0</strong>
                </div>

                <div id="adsbAlertMetric">
                    <span>ALERT</span>
                    <strong id="adsbAlertCount">0</strong>
                </div>
            </div>

            <div class="adsb-receiver-line">
                <span id="adsbReceiverState">
                    ADS-B receiver awaiting data
                </span>

                <span id="adsbSignal">
                    SIG —
                </span>
            </div>

            <div class="adsb-table-wrap">
                <table class="adsb-table">
                    <thead>
                        <tr>
                            <th>CALLSIGN</th>
                            <th>TAIL</th>
                            <th>TYPE</th>
                            <th>ALT</th>
                            <th>KT</th>
                            <th>TRACK</th>
                            <th>V/S</th>
                            <th>SQWK</th>
                        </tr>
                    </thead>

                    <tbody id="adsbRows">
                        <tr>
                            <td colspan="8"
                                class="adsb-empty">
                                Waiting for aircraft...
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div
                id="adsbDetailCard"
                class="adsb-detail-card">
                Select an aircraft.
            </div>

            <button
                id="adsbRawToggle"
                class="adsb-raw-toggle"
                type="button">
                ADVANCED ▸ RAW DECODER
            </button>
        `;

        output.parentNode.insertBefore(
            panel,
            output
        );

        output.style.display = "none";

        el("adsbRawToggle")?.addEventListener(
            "click",
            () => {
                const opening =
                    output.style.display === "none";

                output.style.display =
                    opening ? "block" : "none";

                el("adsbRawToggle").textContent =
                    opening
                        ? "ADVANCED ▾ RAW DECODER"
                        : "ADVANCED ▸ RAW DECODER";
            }
        );
    }

    function renderDetail(track) {
        const target = el("adsbDetailCard");

        if (!target) {
            return;
        }

        if (!track) {
            target.innerHTML =
                `<div class="adsb-detail-empty">
                    Select an aircraft.
                 </div>`;
            return;
        }

        const rate = Number(
            track.vertical_rate_fpm
        );

        let rateText = "—";

        if (Number.isFinite(rate)) {
            rateText =
                `${rate > 0 ? "+" : ""}` +
                `${Math.round(rate)} fpm`;
        }

        const position =
            present(track.latitude) &&
            present(track.longitude)
                ? `${Number(track.latitude).toFixed(4)}, ` +
                  `${Number(track.longitude).toFixed(4)}`
                : "—";

        const alert = emergencyText(
            track.squawk
        );

        target.innerHTML = `
            ${
                alert
                    ? `<div class="adsb-emergency-banner">
                           ${esc(alert)} · SQWK ${esc(track.squawk)}
                       </div>`
                    : ""
            }

            <div class="adsb-detail-heading">
                <div>
                    <strong>
                        ${show(track.callsign)}
                    </strong>

                    <span>
                        ${show(track.registration)}
                    </span>
                </div>

                <div class="adsb-detail-icao">
                    ${show(track.icao)}
                </div>
            </div>

            <div class="adsb-detail-description">
                ${show(track.aircraft_type)}
                ${
                    track.description
                        ? ` · ${esc(track.description)}`
                        : ""
                }
            </div>

            <div class="adsb-detail-grid">
                <span>ALTITUDE</span>
                <strong>
                    ${
                        track.on_ground
                            ? "GROUND"
                            : `${whole(track.altitude_ft)} ft`
                    }
                </strong>

                <span>GROUND SPEED</span>
                <strong>
                    ${
                        present(track.ground_speed_kt)
                            ? `${whole(track.ground_speed_kt)} kt`
                            : "—"
                    }
                </strong>

                <span>TRACK</span>
                <strong>
                    ${direction(track.track_deg)}
                </strong>

                <span>VERTICAL RATE</span>
                <strong>
                    ${rateText}
                </strong>

                <span>SQUAWK</span>
                <strong>
                    ${show(track.squawk)}
                </strong>

                <span>POSITION</span>
                <strong>
                    ${position}
                </strong>

                <span>LAST SEEN</span>
                <strong>
                    ${
                        present(track.seen_seconds)
                            ? `${Number(
                                track.seen_seconds
                              ).toFixed(1)} s`
                            : "—"
                    }
                </strong>

                <span>MESSAGES</span>
                <strong>
                    ${show(track.messages)}
                </strong>
            </div>
        `;
    }

    function renderTracks(data) {
        ensureUI();

        const tracks =
            Array.isArray(data?.aircraft)
                ? [...data.aircraft]
                : [];

        el("adsbTrackCount").textContent =
            data?.aircraft_count ?? tracks.length;

        el("adsbPositionCount").textContent =
            data?.aircraft_with_position ?? 0;

        el("adsbMessageCount").textContent =
            data?.messages ?? 0;

        el("adsbAlertCount").textContent =
            data?.emergency_count ?? 0;

        el("adsbAlertMetric")?.classList.toggle(
            "active",
            Number(data?.emergency_count ?? 0) > 0
        );

        tracks.sort((a, b) => {
            const alertOrder =
                Number(emergency(b)) -
                Number(emergency(a));

            if (alertOrder) {
                return alertOrder;
            }

            return (
                Number(a.seen_seconds ?? 99999) -
                Number(b.seen_seconds ?? 99999)
            );
        });

        const body = el("adsbRows");

        body.replaceChildren();

        if (!tracks.length) {
            const row =
                document.createElement("tr");

            row.innerHTML = `
                <td colspan="8"
                    class="adsb-empty">
                    No active aircraft tracks
                </td>
            `;

            body.appendChild(row);
            renderDetail(null);

            return;
        }

        for (const track of tracks) {
            const row =
                document.createElement("tr");

            if (emergency(track)) {
                row.classList.add(
                    "adsb-alert-row"
                );
            }

            if (
                selectedIcao &&
                selectedIcao === track.icao
            ) {
                row.classList.add(
                    "selected"
                );
            }

            const rate =
                Number(track.vertical_rate_fpm);

            const rateText =
                Number.isFinite(rate)
                    ? `${rate > 0 ? "+" : ""}` +
                      `${Math.round(rate)}`
                    : "—";

            row.innerHTML = `
                <td>${show(track.callsign)}</td>
                <td>${show(track.registration)}</td>
                <td>${show(track.aircraft_type)}</td>

                <td>
                    ${
                        track.on_ground
                            ? "GND"
                            : whole(track.altitude_ft)
                    }
                </td>

                <td>
                    ${whole(track.ground_speed_kt)}
                </td>

                <td>
                    ${direction(track.track_deg)}
                </td>

                <td>
                    ${rateText}
                </td>

                <td>
                    ${show(track.squawk)}
                </td>
            `;

            row.addEventListener(
                "click",
                () => {
                    selectedIcao =
                        track.icao ?? null;

                    body
                        .querySelectorAll("tr")
                        .forEach(
                            candidate =>
                                candidate.classList.remove(
                                    "selected"
                                )
                        );

                    row.classList.add(
                        "selected"
                    );

                    renderDetail(track);
                }
            );

            body.appendChild(row);
        }

        if (selectedIcao) {
            renderDetail(
                tracks.find(
                    track =>
                        track.icao === selectedIcao
                ) ?? null
            );
        }
    }

    function renderStats(stats) {
        const state = el("adsbReceiverState");
        const signal = el("adsbSignal");

        if (state) {
            const valid =
                Number(stats?.messages_valid ?? 0);

            state.textContent =
                valid > 0
                    ? `${valid} valid msg/min`
                    : "Listening on 1090 MHz";
        }

        if (signal) {
            const sig = Number(stats?.signal);
            const noise = Number(stats?.noise);

            const sigText =
                Number.isFinite(sig)
                    ? sig.toFixed(1)
                    : "—";

            const noiseText =
                Number.isFinite(noise)
                    ? noise.toFixed(1)
                    : "—";

            signal.textContent =
                `SIG ${sigText} · NOISE ${noiseText}`;
        }
    }

    async function refresh() {
        ensureUI();

        const tracker = el("adsbTracker");
        const selectedTask =
            el("rfTask")?.value;

        if (selectedTask !== "adsb") {
            if (tracker) {
                tracker.style.display =
                    "none";
            }

            return;
        }

        if (tracker) {
            tracker.style.display =
                "block";
        }

        try {
            const [aircraft, stats] =
                await Promise.all([
                    request(AIRCRAFT_URL),
                    request(STATS_URL),
                ]);

            renderTracks(aircraft);
            renderStats(stats);

        } catch (error) {
            const state =
                el("adsbReceiverState");

            if (state) {
                state.textContent =
                    `ADS-B API: ${error.message}`;
            }
        }
    }

    function mount() {
        ensureUI();

        el("rfTask")?.addEventListener(
            "change",
            refresh
        );

        refresh();

        window.setInterval(
            refresh,
            POLL_MS
        );
    }

    if (
        document.readyState === "loading"
    ) {
        document.addEventListener(
            "DOMContentLoaded",
            mount
        );
    } else {
        mount();
    }
})();
