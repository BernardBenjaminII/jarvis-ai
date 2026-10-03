(() => {
    "use strict";

    const $ = id =>
        document.getElementById(id);

    function ensureAmOption() {
        const task = $("rfTask");

        if (!task) {
            return;
        }

        if (
            task.querySelector(
                'option[value="am"]'
            )
        ) {
            return;
        }

        const option =
            document.createElement(
                "option"
            );

        option.value = "am";
        option.textContent =
            "AM Broadcast";

        const fm =
            task.querySelector(
                'option[value="fm"]'
            );

        if (fm) {
            fm.after(option);
        } else {
            task.appendChild(option);
        }
    }

    function updateButtons() {
        const selected =
            $("rfTask")?.value;

        $("rfRadioModeFm")
            ?.classList.toggle(
                "active",
                selected === "fm"
            );

        $("rfRadioModeAm")
            ?.classList.toggle(
                "active",
                selected === "am"
            );
    }

    function configurePanel(mode) {
        const panel =
            $("rfFmTuner");

        if (!panel) {
            return;
        }

        /*
         * Radio panel must stay visible for
         * either broadcast-radio mode.
         */
        panel.hidden = false;

        const title =
            panel.querySelector(
                ".rf-fm-title strong"
            );

        const range =
            panel.querySelector(
                ".rf-fm-title span"
            );

        const input =
            $("rfFmFrequency");

        if (mode === "am") {

            if (title) {
                title.textContent =
                    "AM RADIO";
            }

            if (range) {
                range.textContent =
                    "531–1602 kHz";
            }

            if (input) {
                input.min = "531";
                input.max = "1602";
                input.step = "9";

                const current =
                    Number(input.value);

                if (
                    !Number.isFinite(current)
                    || current < 531
                    || current > 1602
                ) {
                    input.value = "999";
                }
            }

            const legacy =
                $("rfFrequency");

            if (legacy) {
                const khz =
                    Number(
                        input?.value
                        || 999
                    );

                legacy.value =
                    (
                        khz / 1000
                    ).toFixed(6);
            }

        } else {

            if (title) {
                title.textContent =
                    "FM RADIO";
            }

            if (range) {
                range.textContent =
                    "87.5–108.0 MHz";
            }

            if (input) {
                input.min = "87.5";
                input.max = "108";
                input.step = "0.1";

                const current =
                    Number(input.value);

                if (
                    !Number.isFinite(current)
                    || current < 87.5
                    || current > 108
                ) {
                    input.value = "100.0";
                }
            }

            const legacy =
                $("rfFrequency");

            if (legacy) {
                legacy.value =
                    Number(
                        input?.value
                        || 100
                    ).toFixed(3);
            }
        }
    }

    function selectMode(mode) {
        if (
            mode !== "fm"
            && mode !== "am"
        ) {
            return;
        }

        const task =
            $("rfTask");

        if (!task) {
            return;
        }

        task.value = mode;

        task.dispatchEvent(
            new Event(
                "change",
                {
                    bubbles: true,
                }
            )
        );

        /*
         * Let existing RF listeners finish,
         * then force correct radio presentation.
         */
        setTimeout(
            () => {
                configurePanel(mode);
                updateButtons();
            },
            0
        );
    }

    function mount() {
        ensureAmOption();

        $("rfRadioModeFm")
            ?.addEventListener(
                "click",
                () => {
                    selectMode("fm");
                }
            );

        $("rfRadioModeAm")
            ?.addEventListener(
                "click",
                () => {
                    selectMode("am");
                }
            );

        $("rfTask")
            ?.addEventListener(
                "change",
                () => {
                    const selected =
                        $("rfTask")?.value;

                    updateButtons();

                    if (
                        selected === "fm"
                        || selected === "am"
                    ) {
                        setTimeout(
                            () => {
                                configurePanel(
                                    selected
                                );
                            },
                            0
                        );
                    }
                }
            );

        updateButtons();

        const selected =
            $("rfTask")?.value;

        if (
            selected === "fm"
            || selected === "am"
        ) {
            configurePanel(
                selected
            );
        }
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
