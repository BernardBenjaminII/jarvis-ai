
(() => {
  "use strict";

  const ID = "jarvis-un-news-r17";
  let updating = false;

  function element(tag, className, value) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (value !== undefined) node.textContent = value;
    return node;
  }

  function timeLabel(value) {
    const date = new Date(value);
    return Number.isFinite(date.getTime())
      ? date.toLocaleString()
      : "Publication time unavailable";
  }

  function sourceUrl(event) {
    const url = event.source?.url;
    try {
      const parsed = new URL(url);
      return parsed.protocol === "https:" &&
        parsed.hostname === "news.un.org"
        ? parsed.href : null;
    } catch {
      return null;
    }
  }

  async function update() {
    if (updating) return;
    updating = true;

    const root = document.getElementById(ID);
    if (!root) {
      updating = false;
      return;
    }

    const status = root.querySelector(".un-status");
    const list = root.querySelector(".un-list");

    try {
      const response = await fetch("/operations/sitrep", {
        cache: "no-store",
        headers: {Accept: "application/json"},
        signal: AbortSignal.timeout(20000)
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();

      const provider = (data.sources || []).find(
        s => s.provider_id === "un_peace_security"
      );

      const reports = (data.security_events || [])
        .filter(e =>
          e.source?.provider_id === "un_peace_security"
        )
        .sort((a, b) =>
          new Date(b.published_at) - new Date(a.published_at)
        );

      const live = provider?.state === "LIVE";

      status.textContent = live ? "SOURCE LIVE" :
        provider ? `SOURCE ${provider.state}` : "SOURCE UNAVAILABLE";

      status.dataset.state = live ? "live" : "unavailable";

      root.querySelector(".un-count").textContent =
        `${reports.length} reports · latest 5 displayed`;

      list.replaceChildren();

      if (!reports.length) {
        list.append(
          element("p", "un-empty", "No UN reports available.")
        );
        return;
      }

      for (const report of reports.slice(0, 5)) {
        const item = element("article", "un-item");
        const heading = element("h4", "", report.title || "Untitled report");
        const url = sourceUrl(report);

        if (url) {
          const link = element("a", "", heading.textContent);
          link.href = url;
          link.target = "_blank";
          link.rel = "noopener noreferrer";
          heading.replaceChildren(link);
        }

        const summary = element(
          "p", "un-summary", report.summary || "No summary available."
        );

        const meta = element(
          "p", "un-meta",
          `UN News · ${timeLabel(report.published_at)} · ${
            report.verification || "Publisher report"
          }`
        );

        item.append(heading, summary, meta);
        list.append(item);
      }

      root.querySelector(".un-updated").textContent =
        `Brief updated ${new Date().toLocaleTimeString()}`;

    } catch (error) {
      status.textContent = "DATA UNAVAILABLE";
      status.dataset.state = "unavailable";
      root.querySelector(".un-updated").textContent =
        `Unable to refresh: ${error.message}`;
    } finally {
      updating = false;
    }
  }

  function mount() {
    if (document.getElementById(ID)) return true;

    const shell = document.getElementById("jarvis-r32-shell");
    const radio = document.getElementById("jarvis-radio");
    const operations = document.getElementById("jarvis-r32-operations");

    if (!shell || !operations || operations.parentElement !== shell)
      return false;

    const section = element("section", "jarvis-un-news");
    section.id = ID;
    section.setAttribute("aria-label", "UN Peace and Security Brief");

    const header = element("div", "un-header");
    const title = element("div");

    title.append(
      element("small", "", "GLOBAL INTELLIGENCE"),
      element("h3", "", "UN News · Peace & Security")
    );

    const status = element("span", "un-status", "CONNECTING");
    header.append(title, status);

    const count = element("p", "un-count", "Loading reports...");
    const list = element("div", "un-list");
    const footer = element("div", "un-footer");
    const updated = element("small", "un-updated", "");

    const refresh = element("button", "", "Refresh");
    refresh.type = "button";
    refresh.addEventListener("click", update);

    footer.append(updated, refresh);
    section.append(header, count, list, footer);

    if (radio?.parentElement === shell) {
      radio.insertAdjacentElement("afterend", section);
    } else {
      shell.insertBefore(section, operations);
    }

    update();
    setInterval(update, 60000);
    return true;
  }

  function initialize() {
    if (mount()) return;

    let attempts = 0;
    const interval = setInterval(() => {
      attempts++;
      if (mount() || attempts >= 30) clearInterval(interval);
    }, 1000);
  }

  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", initialize, {once: true});
  else
    initialize();
})();
