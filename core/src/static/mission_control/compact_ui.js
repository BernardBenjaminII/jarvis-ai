"use strict";
(() => {
    const byId = (id) => document.getElementById(id);
    const text = (id, fallback = "—") => byId(id)?.textContent?.trim() || fallback;

    function makeCollapsible(headingId, summaryBuilder, expanded = false) {
        const heading = byId(headingId);
        const section = heading?.closest(".dashboard-section");
        const header = heading?.closest(".section-header");
        if (!section || !header || section.dataset.compactReady === "true") return;

        section.dataset.compactReady = "true";
        section.dataset.expanded = String(expanded);
        section.classList.add("compact-dashboard-section");

        const body = document.createElement("div");
        body.className = "compact-section-body";
        while (header.nextSibling) body.appendChild(header.nextSibling);
        section.appendChild(body);
        body.hidden = !expanded;

        const summary = document.createElement("p");
        summary.className = "compact-section-summary";
        header.appendChild(summary);

        const toggle = document.createElement("button");
        toggle.type = "button";
        toggle.className = "compact-section-toggle";
        toggle.setAttribute("aria-label", `Toggle ${heading.textContent.trim()} details`);
        toggle.setAttribute("aria-expanded", String(expanded));
        header.appendChild(toggle);

        const updateSummary = () => {
            const next = summaryBuilder();
            if (summary.textContent !== next) summary.textContent = next;
        };
        const setExpanded = (value) => {
            section.dataset.expanded = String(value);
            body.hidden = !value;
            toggle.setAttribute("aria-expanded", String(value));
        };
        const toggleSection = () => setExpanded(section.dataset.expanded !== "true");

        toggle.addEventListener("click", (event) => {
            event.stopPropagation();
            toggleSection();
        });
        header.addEventListener("click", (event) => {
            if (event.target.closest("button,a")) return;
            toggleSection();
        });

        updateSummary();
        const observer = new MutationObserver(updateSummary);
        observer.observe(body, {
            subtree: true,
            childList: true,
            characterData: true,
            attributes: true,
        });
    }

    function installGroundingMetrics() {
        const metrics = document.querySelector(".knowledge-result-metrics");
        if (!metrics || byId("knowledge-citations")) return;

        const citation = document.createElement("div");
        citation.innerHTML = '<dt>Citations</dt><dd id="knowledge-citations">0</dd>';
        metrics.appendChild(citation);

        const conflicts = document.createElement("div");
        conflicts.innerHTML = '<dt>Conflicts</dt><dd id="knowledge-conflicts">0</dd>';
        metrics.appendChild(conflicts);

        const accepted = document.createElement("div");
        accepted.className = "knowledge-grounding-secondary";
        accepted.innerHTML = '<dt>Accepted</dt><dd id="knowledge-accepted">0</dd>';
        metrics.appendChild(accepted);

        const sync = () => {
            const map = [
                ["ga-citations", "knowledge-citations"],
                ["ga-conflicts", "knowledge-conflicts"],
                ["ga-accepted", "knowledge-accepted"],
            ];
            for (const [source, target] of map) {
                if (byId(source) && byId(target)) byId(target).textContent = text(source, "0");
            }
        };

        sync();
        const telemetry = byId("grounded-answer-projection");
        if (telemetry) {
            new MutationObserver(sync).observe(telemetry, {
                subtree: true,
                childList: true,
                characterData: true,
                attributes: true,
            });
        }
    }

    function installStatusDisclosure() {
        const banner = byId("executive-status-banner");
        if (!banner || banner.dataset.compactStatusReady === "true") return;
        banner.dataset.compactStatusReady = "true";
        banner.tabIndex = 0;
        banner.setAttribute("role", "button");
        banner.setAttribute("aria-expanded", "false");
        banner.title = "Click for Executive status details";

        const toggle = () => {
            const expanded = banner.dataset.expanded === "true";
            banner.dataset.expanded = String(!expanded);
            banner.setAttribute("aria-expanded", String(!expanded));
        };
        banner.addEventListener("click", toggle);
        banner.addEventListener("keydown", (event) => {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                toggle();
            }
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        makeCollapsible("enterprise-summary-heading", () =>
            `Knowledge ${text("metric-knowledge-value")} · Missions ${text("metric-missions-value")} · Assets ${text("metric-assets-value")} · AI ${text("metric-ai-models-value")} · Events ${text("metric-executive-events-value")}`
        );

        makeCollapsible("operational-picture-heading", () =>
            `Health ${text("executive-health-state")} · Root ${text("storage-root-percent")} · Project ${text("storage-project-percent")} · Load ${text("runtime-system-load")}`
        );

        makeCollapsible("executive-activity-heading", () =>
            `Events ${text("metric-executive-events-value")} · Mission ${text("readiness-mission-state", "—")} · Knowledge ${text("readiness-knowledge-state", "—")}`
        );

        makeCollapsible("workstreams-heading", () =>
            `Knowledge ${text("metric-knowledge-value")} · Missions ${text("metric-missions-value")} · AI ${text("metric-ai-models-value")} · Robotics ${text("metric-robots-value")}`
        );

        installStatusDisclosure();

        // Grounded Answer Telemetry is fetched as before, but its useful
        // bottom-line values are surfaced contextually beneath the answer.
        setTimeout(installGroundingMetrics, 0);
        setTimeout(installGroundingMetrics, 250);
    });
})();
