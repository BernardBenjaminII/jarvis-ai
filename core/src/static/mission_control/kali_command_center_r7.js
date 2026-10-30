(() => {
  "use strict";

  const ENDPOINT = "/api/bounty-agent/platform";
  const POLL_MS = 120;
  const POLL_LIMIT = 50;

  const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[c]));

  async function getPlatform() {
    const response = await fetch(ENDPOINT, {
      headers: { "Accept": "application/json" },
      cache: "no-store"
    });
    if (!response.ok) throw new Error(`Platform endpoint returned ${response.status}`);
    return response.json();
  }

  function findWorkspaceButton(name) {
    return document.querySelector(`button[data-workspace="${name}"]`);
  }

  function waitForWorkspaceButton(name) {
    return new Promise((resolve) => {
      let count = 0;
      const tick = () => {
        const button = findWorkspaceButton(name);
        if (button || count++ >= POLL_LIMIT) {
          resolve(button || null);
          return;
        }
        setTimeout(tick, POLL_MS);
      };
      tick();
    });
  }

  function makeShell(info, bountyButton) {
    if (document.getElementById("jarvis-kali-r7-bar")) return;

    const bar = document.createElement("section");
    bar.id = "jarvis-kali-r7-bar";
    bar.className = "jarvis-kali-r7-bar";
    bar.setAttribute("aria-label", "Kali operations workspace");

    bar.innerHTML = `
      <div class="jk7-identity">
        <span class="jk7-dot" aria-hidden="true"></span>
        <div>
          <small>DETECTED HOST · ${esc((info.environment || "unknown").toUpperCase())}</small>
          <strong>JARVIS — KALI OPERATIONS CENTER</strong>
        </div>
      </div>
      <div class="jk7-meta">
        <span>${esc(info.pretty_name || "Kali GNU/Linux")}</span>
        <span class="jk7-status">${info.live_bounty_enabled ? "BOUNTY EXECUTION ENABLED" : "REVIEW ONLY"}</span>
      </div>
      <nav class="jk7-nav" aria-label="Kali workspaces">
        <button type="button" data-r7-open="bounty-agent">Bug Bounty</button>
        <button type="button" data-r7-open="knowledge">Knowledge</button>
        <button type="button" data-r7-open="system">System</button>
      </nav>
    `;

    const anchor =
      document.querySelector("main") ||
      document.querySelector("#app") ||
      document.body.firstElementChild;

    if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(bar, anchor);
    else document.body.prepend(bar);

    const bounty = bar.querySelector('[data-r7-open="bounty-agent"]');
    bounty.disabled = !bountyButton || !info.live_bounty_enabled;
    bounty.title = bountyButton
      ? "Open the existing Jarvis Bug Bounty Agent workspace"
      : "Bug Bounty workspace launcher was not found";
    bounty.addEventListener("click", () => bountyButton?.click());

    bar.querySelector('[data-r7-open="knowledge"]').addEventListener("click", () => {
      const btn = findWorkspaceButton("knowledge");
      if (btn) btn.click();
      else window.location.hash = "knowledge";
    });

    bar.querySelector('[data-r7-open="system"]').addEventListener("click", () => {
      const btn = findWorkspaceButton("system");
      if (btn) btn.click();
    });

    document.title = "JARVIS — Kali Operations Center";
  }

  function suppressKaliOnlyUIWhenNotKali(info, bountyButton) {
    if ((info.environment || "").toLowerCase() === "kali") return false;
    if (bountyButton) {
      bountyButton.hidden = true;
      bountyButton.disabled = true;
      bountyButton.setAttribute("aria-hidden", "true");
    }
    document.body.dataset.jarvisPlatform = info.environment || "unknown";
    return true;
  }

  async function boot() {
    let info;
    try {
      info = await getPlatform();
    } catch (error) {
      console.warn("JARVIS R7 platform detection unavailable:", error);
      return;
    }

    const bountyButton = await waitForWorkspaceButton("bounty-agent");

    if (suppressKaliOnlyUIWhenNotKali(info, bountyButton)) return;

    document.body.dataset.jarvisPlatform = "kali";
    document.body.classList.add("jarvis-platform-kali", "jarvis-kali-r7");

    if (bountyButton) {
      bountyButton.hidden = false;
      bountyButton.disabled = false;
      bountyButton.classList.add("jarvis-kali-bounty-launcher");
    }

    makeShell(info, bountyButton);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }
})();
