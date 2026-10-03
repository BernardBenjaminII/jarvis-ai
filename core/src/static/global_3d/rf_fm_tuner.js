(() => {
    "use strict";

    const CONFIG = {
        fm: {
            title: "FM RADIO",
            unit: "MHz",

            min: 87.5,
            max: 108.0,

            step: 0.1,
            bigStep: 1.0,

            decimals: 1,

            defaultValue: 100.0,
        },

        am: {
            title: "AM RADIO",
            unit: "kHz",

            min: 531,
            max: 1602,

            step: 9,
            bigStep: 90,

            decimals: 0,

            defaultValue: 999,
        },
    };

    const DETECTED_KEY =
        "jarvis.rf.fm.detected.v1";

    let detectedFM =
        load(DETECTED_KEY);

    let lastStatus = null;

    function el(id) {
        return document.getElementById(id);
    }

    function task() {
        return el("rfTask")?.value
            || "fm";
    }

    function mode() {
        return task() === "am"
            ? "am"
            : "fm";
    }

    function cfg() {
        return CONFIG[mode()];
    }

    function load(key) {
        try {
            const value = JSON.parse(
                localStorage.getItem(key)
                || "[]"
            );

            return Array.isArray(value)
                ? value
                : [];

        } catch {
            return [];
        }
    }

    function save(
        key,
        value
    ) {
        localStorage.setItem(
            key,
            JSON.stringify(value)
        );
    }

    function favoritesKey() {
        return (
            `jarvis.rf.radio.`
            + `${mode()}.favorites.v1`
        );
    }

    function favorites() {
        return load(
            favoritesKey()
        );
    }

    function setFavorites(
        values
    ) {
        save(
            favoritesKey(),
            values
        );
    }

    function normalize(
        value,
        config = cfg()
    ) {
        let number =
            Number(value);

        if (!Number.isFinite(number)) {
            number =
                config.defaultValue;
        }

        number =
            Math.max(
                config.min,
                Math.min(
                    config.max,
                    number
                )
            );

        const steps =
            Math.round(
                (
                    number
                    - config.min
                )
                / config.step
            );

        number =
            config.min
            + steps
            * config.step;

        return Number(
            number.toFixed(
                config.decimals
            )
        );
    }

    function toMHz(
        displayValue,
        selectedMode = mode()
    ) {
        if (
            selectedMode === "am"
        ) {
            return (
                Number(
                    displayValue
                )
                / 1000
            );
        }

        return Number(
            displayValue
        );
    }

    function fromMHz(
        mhz,
        selectedMode = mode()
    ) {
        if (
            selectedMode === "am"
        ) {
            return (
                Number(mhz)
                * 1000
            );
        }

        return Number(
            mhz
        );
    }

    function current() {
        return normalize(
            el("rfFmFrequency")?.value
        );
    }

    function setFrequency(
        value,
        announce = true
    ) {
        const config = cfg();

        const frequency =
            normalize(
                value,
                config
            );

        const tuner =
            el("rfFmFrequency");

        if (tuner) {
            tuner.value =
                frequency.toFixed(
                    config.decimals
                );
        }

        const main =
            el("rfFrequency");

        if (main) {
            main.value =
                toMHz(
                    frequency
                ).toFixed(6);
        }

        highlight();

        if (
            announce
            && el("rfDetail")
        ) {
            el("rfDetail")
                .textContent =
                `${config.title} `
                + `${frequency.toFixed(
                    config.decimals
                )} `
                + config.unit
                + " selected";
        }

        return frequency;
    }

    async function tune(
        value
    ) {
        const selectedMode =
            mode();

        const selector =
            el("rfTask");

        if (
            selector
            && selector.value
                !== selectedMode
        ) {
            selector.value =
                selectedMode;

            selector.dispatchEvent(
                new Event(
                    "change",
                    {
                        bubbles: true,
                    }
                )
            );
        }

        /*
         * The task change listener may reset
         * the legacy frequency control.
         */

        setFrequency(
            value
        );

        if (
            window.JarvisRF
            && typeof (
                window.JarvisRF
                    .startTask
            ) === "function"
        ) {
            await (
                window.JarvisRF
                    .startTask()
            );
        }
    }

    function unique(
        values,
        selectedMode = mode()
    ) {
        const config =
            CONFIG[selectedMode];

        return [
            ...new Set(
                values
                    .map(
                        value =>
                            normalize(
                                value,
                                config
                            )
                    )
                    .map(
                        value =>
                            value.toFixed(
                                config.decimals
                            )
                    )
            ),
        ]
            .map(Number)
            .sort(
                (a, b) =>
                    a - b
            );
    }

    function renderChannels(
        id,
        values,
        emptyMessage
    ) {
        const container =
            el(id);

        if (!container) {
            return;
        }

        container.innerHTML = "";

        if (!values.length) {
            const empty =
                document.createElement(
                    "span"
                );

            empty.className =
                "rf-fm-empty";

            empty.textContent =
                emptyMessage;

            container.appendChild(
                empty
            );

            return;
        }

        const config = cfg();

        values.forEach(
            frequency => {
                const button =
                    document.createElement(
                        "button"
                    );

                button.type =
                    "button";

                button.className =
                    "rf-fm-channel";

                button.dataset.frequency =
                    frequency.toFixed(
                        config.decimals
                    );

                button.textContent =
                    frequency.toFixed(
                        config.decimals
                    );

                button.title =
                    `Tune ${frequency.toFixed(
                        config.decimals
                    )} ${config.unit}`;

                button.addEventListener(
                    "click",
                    () =>
                        tune(
                            frequency
                        )
                );

                container.appendChild(
                    button
                );
            }
        );

        highlight();
    }

    function highlight() {
        const config = cfg();

        const frequency =
            current().toFixed(
                config.decimals
            );

        document
            .querySelectorAll(
                ".rf-fm-channel"
            )
            .forEach(
                button => {
                    button.classList
                        .toggle(
                            "active",
                            button.dataset
                                .frequency
                                === frequency
                        );
                }
            );
    }

    function renderFavorites() {
        renderChannels(
            "rfFmFavorites",
            favorites(),
            "No saved channels."
        );
    }

    function renderDetected() {
        const label =
            document.querySelector(
                ".rf-fm-section-label"
            );

        const container =
            el("rfFmDetected");

        if (
            mode() === "am"
        ) {
            if (label) {
                label.style.display =
                    "none";
            }

            if (container) {
                container.style.display =
                    "none";
            }

            return;
        }

        if (label) {
            label.style.display =
                "";
        }

        if (container) {
            container.style.display =
                "";
        }

        renderChannels(
            "rfFmDetected",
            detectedFM,
            "Run an FM spectrum scan first."
        );
    }

    function renderAll() {
        renderDetected();
        renderFavorites();
    }

    function saveFavorite() {
        const list =
            unique(
                [
                    ...favorites(),
                    current(),
                ]
            );

        setFavorites(
            list
        );

        renderFavorites();
    }

    function updateStepButtons() {
        const config = cfg();

        const buttons = [
            ...document.querySelectorAll(
                "[data-fm-step]"
            ),
        ];

        const values = [
            -config.bigStep,
            -config.step,
            config.step,
            config.bigStep,
        ];

        buttons.forEach(
            (button, index) => {
                const value =
                    values[index];

                if (
                    value
                    === undefined
                ) {
                    return;
                }

                button.dataset.fmStep =
                    String(value);

                const sign =
                    value > 0
                        ? "+"
                        : "";

                button.textContent =
                    sign
                    + value.toFixed(
                        config.decimals
                    );
            }
        );
    }

    function updateModeUI() {
        const radio =
            el("rfFmTuner");

        const selected =
            task();

        if (!radio) {
            return;
        }

        if (
            selected !== "fm"
            && selected !== "am"
        ) {
            radio.hidden = true;
            return;
        }

        radio.hidden = false;

        const config = cfg();

        const title =
            radio.querySelector(
                ".rf-fm-title strong"
            );

        const range =
            radio.querySelector(
                ".rf-fm-title span"
            );

        if (title) {
            title.textContent =
                config.title;
        }

        if (range) {
            range.textContent =
                `${config.min}–`
                + `${config.max} `
                + config.unit;
        }

        const input =
            el("rfFmFrequency");

        if (input) {
            input.min =
                config.min;

            input.max =
                config.max;

            input.step =
                config.step;
        }

        const select =
            el("rfFmSelect");

        if (select) {
            select.textContent =
                "TUNE";
        }

        updateStepButtons();

        const legacy =
            Number(
                el("rfFrequency")?.value
            );

        if (
            Number.isFinite(
                legacy
            )
        ) {
            setFrequency(
                fromMHz(
                    legacy
                ),
                false
            );
        } else {
            setFrequency(
                config.defaultValue,
                false
            );
        }

        renderAll();
        renderAudioStatus(
            lastStatus
        );
    }

    function step(
        delta
    ) {
        setFrequency(
            current()
            + Number(delta)
        );
    }

    function previousNext(
        direction
    ) {
        if (
            mode() === "am"
            || !detectedFM.length
        ) {
            tune(
                current()
                + cfg().step
                * direction
            );

            return;
        }

        const value =
            current();

        let target;

        if (direction > 0) {
            target =
                detectedFM.find(
                    item =>
                        item
                        > value + 0.01
                );

            if (
                target
                === undefined
            ) {
                target =
                    detectedFM[0];
            }

        } else {
            target =
                [...detectedFM]
                    .reverse()
                    .find(
                        item =>
                            item
                            < value - 0.01
                    );

            if (
                target
                === undefined
            ) {
                target =
                    detectedFM[
                        detectedFM.length
                        - 1
                    ];
            }
        }

        tune(
            target
        );
    }

    function spectrumReceived(
        event
    ) {
        const spectrum =
            event.detail;

        if (
            !spectrum
            || !Array.isArray(
                spectrum.peaks
            )
        ) {
            return;
        }

        const values =
            spectrum.peaks
                .map(
                    peak =>
                        Number(
                            peak.frequency
                        )
                        / 1_000_000
                )
                .filter(
                    value =>
                        Number.isFinite(
                            value
                        )
                        && value >= 87.5
                        && value <= 108
                );

        if (!values.length) {
            return;
        }

        detectedFM =
            unique(
                values,
                "fm"
            );

        save(
            DETECTED_KEY,
            detectedFM
        );

        if (
            mode() === "fm"
        ) {
            renderDetected();
        }
    }

    function ensureAudioStatus() {
        if (
            el("rfRadioAudioStatus")
        ) {
            return;
        }

        const tuner =
            el("rfFmTuner");

        if (!tuner) {
            return;
        }

        const node =
            document.createElement(
                "div"
            );

        node.id =
            "rfRadioAudioStatus";

        node.className =
            "rf-radio-audio-status";

        node.innerHTML = `
            <span>AUDIO</span>
            <strong id="rfRadioAudioState">
                STOPPED
            </strong>
            <span id="rfRadioAudioOutput">
                system default
            </span>
        `;

        const detectedLabel =
            tuner.querySelector(
                ".rf-fm-section-label"
            );

        if (detectedLabel) {
            detectedLabel.before(
                node
            );
        } else {
            tuner.appendChild(
                node
            );
        }
    }

    function renderAudioStatus(
        status
    ) {
        if (!status) {
            return;
        }

        const state =
            el(
                "rfRadioAudioState"
            );

        const output =
            el(
                "rfRadioAudioOutput"
            );

        if (state) {
            if (
                status.audio_state
                === "playing"
            ) {
                state.textContent =
                    "PLAYING";

            } else if (
                status.state
                === "error"
            ) {
                state.textContent =
                    "ERROR";

            } else {
                state.textContent =
                    "STOPPED";
            }
        }

        if (output) {
            const parts = [];

            if (
                status.audio_rate_hz
            ) {
                parts.push(
                    `${
                        status.audio_rate_hz
                        / 1000
                    } kHz`
                );
            }

            if (
                status.audio_output
            ) {
                parts.push(
                    status.audio_output
                );
            }

            output.textContent =
                parts.join(" · ")
                || "system default";
        }
    }

    function statusReceived(
        event
    ) {
        lastStatus =
            event.detail;

        renderAudioStatus(
            lastStatus
        );
    }

    function mount() {
        if (!el("rfFmTuner")) {
            return;
        }

        ensureAudioStatus();

        el("rfTask")
            ?.addEventListener(
                "change",
                updateModeUI
            );

        el("rfFmFrequency")
            ?.addEventListener(
                "change",
                event =>
                    setFrequency(
                        event.target
                            .value
                    )
            );

        el("rfFmFrequency")
            ?.addEventListener(
                "keydown",
                event => {
                    if (
                        event.key
                        === "Enter"
                    ) {
                        tune(
                            event.target
                                .value
                        );
                    }
                }
            );

        document
            .querySelectorAll(
                "[data-fm-step]"
            )
            .forEach(
                button => {
                    button.addEventListener(
                        "click",
                        () =>
                            step(
                                button.dataset
                                    .fmStep
                            )
                    );
                }
            );

        el("rfFmPrevPeak")
            ?.addEventListener(
                "click",
                () =>
                    previousNext(-1)
            );

        el("rfFmNextPeak")
            ?.addEventListener(
                "click",
                () =>
                    previousNext(1)
            );

        el("rfFmSelect")
            ?.addEventListener(
                "click",
                () =>
                    tune(
                        current()
                    )
            );

        el("rfFmSaveFavorite")
            ?.addEventListener(
                "click",
                saveFavorite
            );

        window.addEventListener(
            "jarvis:rf-spectrum",
            spectrumReceived
        );

        window.addEventListener(
            "jarvis:rf-status",
            statusReceived
        );

        updateModeUI();
    }

    if (
        document.readyState
        === "loading"
    ) {
        document.addEventListener(
            "DOMContentLoaded",
            mount,
            {
                once: true,
            }
        );
    } else {
        mount();
    }
})();
