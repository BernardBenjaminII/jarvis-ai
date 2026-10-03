(() => {
    "use strict";

    const PANEL_ID = "rfSwitchboard";

    function panel() {
        return document.getElementById(
            PANEL_ID
        );
    }

    function ensureExpandButton() {
        const rf = panel();

        if (!rf) {
            return;
        }

        const header =
            rf.querySelector(
                ".rf-header"
            );

        if (!header) {
            return;
        }

        if (
            document.getElementById(
                "rfExpandToggle"
            )
        ) {
            return;
        }

        const button =
            document.createElement(
                "button"
            );

        button.id =
            "rfExpandToggle";

        button.type =
            "button";

        button.className =
            "rf-expand-toggle";

        button.title =
            "Expand RF console";

        button.setAttribute(
            "aria-label",
            "Expand RF console"
        );

        button.textContent =
            "EXPAND";

        header.appendChild(
            button
        );

        button.addEventListener(
            "click",
            toggle
        );
    }

    function ensureCloseButton() {
        const rf = panel();

        if (!rf) {
            return;
        }

        if (
            document.getElementById(
                "rfExpandedClose"
            )
        ) {
            return;
        }

        const button =
            document.createElement(
                "button"
            );

        button.id =
            "rfExpandedClose";

        button.type =
            "button";

        button.className =
            "rf-expanded-close";

        button.title =
            "Close expanded RF console";

        button.textContent =
            "×";

        button.addEventListener(
            "click",
            collapse
        );

        rf.appendChild(
            button
        );
    }

    function ensureBackdrop() {
        if (
            document.getElementById(
                "rfPanelBackdrop"
            )
        ) {
            return;
        }

        const backdrop =
            document.createElement(
                "div"
            );

        backdrop.id =
            "rfPanelBackdrop";

        backdrop.className =
            "rf-panel-backdrop";

        backdrop.addEventListener(
            "click",
            collapse
        );

        document.body.appendChild(
            backdrop
        );
    }

    function expanded() {
        return panel()
            ?.classList.contains(
                "rf-expanded"
            );
    }

    function expand() {
        const rf = panel();

        if (!rf) {
            return;
        }

        ensureCloseButton();
        ensureBackdrop();

        rf.classList.add(
            "rf-expanded"
        );

        document.body.classList.add(
            "rf-console-open"
        );

        const toggle =
            document.getElementById(
                "rfExpandToggle"
            );

        if (toggle) {
            toggle.textContent =
                "COLLAPSE";

            toggle.title =
                "Collapse RF console";
        }
    }

    function collapse() {
        const rf = panel();

        if (!rf) {
            return;
        }

        rf.classList.remove(
            "rf-expanded"
        );

        document.body.classList.remove(
            "rf-console-open"
        );

        const toggle =
            document.getElementById(
                "rfExpandToggle"
            );

        if (toggle) {
            toggle.textContent =
                "EXPAND";

            toggle.title =
                "Expand RF console";
        }
    }

    function toggle() {
        if (expanded()) {
            collapse();
        } else {
            expand();
        }
    }

    function mount() {
        const rf = panel();

        if (!rf) {
            return;
        }

        ensureExpandButton();
        ensureCloseButton();
        ensureBackdrop();

        document.addEventListener(
            "keydown",
            event => {
                if (
                    event.key === "Escape"
                    && expanded()
                ) {
                    collapse();
                }
            }
        );
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
