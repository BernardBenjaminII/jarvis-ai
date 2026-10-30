(() => {
  "use strict";

  const ENDPOINT = "/api/platform-workspace";

  const WORKSPACE_BINDINGS = {
    bounties: "bounty-agent",
    knowledge: "knowledge",
    system: "system",

    missions: "missions",
    targets: "targets",
    recon: "recon",
    findings: "findings",
    agents: "agents",
    intelligence: "intelligence",
    arsenal: "arsenal",
    terminal: "terminal",
  };

  const esc = (value) =>
    String(value ?? "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    }[c]));

  async function getWorkspaceProfile() {
    const response = await fetch(ENDPOINT, {
      headers: {
        Accept: "application/json",
      },
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(
        `Platform workspace endpoint returned ${response.status}`
      );
    }

    return response.json();
  }

  function findWorkspaceButton(name) {
    if (!name) return null;

    return document.querySelector(
      `button[data-workspace="${CSS.escape(name)}"]`
    );
  }

  function resolveLauncher(workspaceId) {
    const existingName =
      WORKSPACE_BINDINGS[workspaceId] || workspaceId;

    return findWorkspaceButton(existingName);
  }

  function openWorkspace(workspaceId) {
    const launcher = resolveLauncher(workspaceId);

    if (launcher) {
      launcher.click();
      return true;
    }

    if (workspaceId === "knowledge") {
      window.location.hash = "knowledge";
      return true;
    }

    return false;
  }

  function capabilityFor(workspace, id) {
    return workspace.capabilities?.[id] || {
      id,
      label: id,
      enabled: false,
      execution: false,
      description: "",
    };
  }

  function makeNavigation(workspace) {
    const nav = document.createElement("nav");

    nav.className = "jk8-nav";
    nav.setAttribute(
      "aria-label",
      `${workspace.label || "Platform"} workspaces`
    );

    for (const id of workspace.navigation || []) {
      const capability = capabilityFor(workspace, id);

      if (!capability.enabled) continue;

      const button = document.createElement("button");

      button.type = "button";
      button.dataset.r8Open = id;
      button.textContent = capability.label || id;

      if (capability.description) {
        button.title = capability.description;
      }

      const launcher = resolveLauncher(id);
      const hasFallback = id === "knowledge";
      const available = Boolean(launcher || hasFallback);

      if (!available) {
        button.disabled = true;
        button.classList.add("jk8-unbound");

        button.title =
          `${capability.description || capability.label || id} ` +
          "— workspace adapter not yet installed";
      }

      if (capability.execution) {
        button.dataset.execution = "true";
      }

      button.addEventListener("click", () => {
        openWorkspace(id);
      });

      nav.appendChild(button);
    }

    return nav;
  }

  function removeLegacyShell() {
    document.getElementById("jarvis-kali-r7-bar")?.remove();
  }

  function suppressKaliExecutionUI() {
    const bountyButton = findWorkspaceButton("bounty-agent");

    if (bountyButton) {
      bountyButton.hidden = true;
      bountyButton.disabled = true;
      bountyButton.setAttribute("aria-hidden", "true");
    }
  }

  function exposeKaliExecutionUI() {
    const bountyButton = findWorkspaceButton("bounty-agent");

    if (bountyButton) {
      bountyButton.hidden = false;
      bountyButton.disabled = false;
      bountyButton.removeAttribute("aria-hidden");
      bountyButton.classList.add("jarvis-kali-bounty-launcher");
    }
  }

  function makeShell(payload) {
    const info = payload.platform || {};
    const workspace = payload.workspace || {};

    if (document.getElementById("jarvis-kali-r8-bar")) {
      return;
    }

    removeLegacyShell();

    const bar = document.createElement("section");

    bar.id = "jarvis-kali-r8-bar";
    bar.className = "jarvis-kali-r8-bar";
    bar.setAttribute(
      "aria-label",
      "Kali operations workspace"
    );

    const environment =
      String(
        info.environment ||
        workspace.platform ||
        "unknown"
      ).toUpperCase();

    const identity = document.createElement("div");
    identity.className = "jk8-identity";

    identity.innerHTML = `
      <span class="jk8-dot" aria-hidden="true"></span>
      <div>
        <small>
          DETECTED HOST · ${esc(environment)}
        </small>
        <strong>
          JARVIS — ${esc(
            (workspace.label || "KALI OPERATIONS CENTER").toUpperCase()
          )}
        </strong>
      </div>
    `;

    const meta = document.createElement("div");
    meta.className = "jk8-meta";

    const stance =
      String(workspace.stance || "general").toUpperCase();

    const executionStatus =
      workspace.execution_enabled
        ? "SECURITY EXECUTION ENABLED"
        : "REVIEW ONLY";

    meta.innerHTML = `
      <span class="jk8-profile">
        ${esc(workspace.workspace_id || "unknown")}
      </span>
      <span>
        ${esc(stance)}
      </span>
      <span class="jk8-status">
        ${esc(executionStatus)}
      </span>
    `;

    const nav = makeNavigation(workspace);
    // JARVIS_KALI_R852_GLOBAL3D
    // Reuse the existing Global 3D application.
    const global3dLink = document.createElement("a");
    global3dLink.href = "/global-3d";
    global3dLink.target = "_blank";
    global3dLink.rel = "noopener noreferrer";
    global3dLink.className = "jk8-global3d";
    global3dLink.textContent = "Global 3D ↗";
    global3dLink.title = "Open the shared Global 3D workspace";
    nav.appendChild(global3dLink);


    bar.appendChild(identity);
    bar.appendChild(meta);
    bar.appendChild(nav);

    const anchor =
      document.querySelector("main") ||
      document.querySelector("#app") ||
      document.body.firstElementChild;

    if (anchor && anchor.parentNode) {
      anchor.parentNode.insertBefore(bar, anchor);
    } else {
      document.body.prepend(bar);
    }
  }

  function applyPlatformState(payload) {
    const info = payload.platform || {};
    const workspace = payload.workspace || {};

    const environment = String(
      info.environment ||
      workspace.platform ||
      "unknown"
    ).toLowerCase();

    document.body.dataset.jarvisPlatform = environment;
    document.body.dataset.jarvisWorkspace =
      workspace.workspace_id || "unknown";

    const isKali =
      environment === "kali" &&
      workspace.workspace_id === "kali-security";

    if (!isKali) {
      suppressKaliExecutionUI();
      return false;
    }

    exposeKaliExecutionUI();

    document.body.classList.add(
      "jarvis-platform-kali",
      "jarvis-kali-r8"
    );

    return true;
  }

  function refreshBindings() {
    const bar = document.getElementById(
      "jarvis-kali-r8-bar"
    );

    if (!bar) return;

    for (const button of bar.querySelectorAll(
      "button[data-r8-open]"
    )) {
      const id = button.dataset.r8Open;
      const launcher = resolveLauncher(id);
      const hasFallback = id === "knowledge";

      if (launcher || hasFallback) {
        button.disabled = false;
        button.classList.remove("jk8-unbound");
      }
    }
  }

  async function boot() {
    let payload;

    try {
      payload = await getWorkspaceProfile();
    } catch (error) {
      console.warn(
        "JARVIS R8 workspace detection unavailable:",
        error
      );

      suppressKaliExecutionUI();
      return;
    }

    if (!applyPlatformState(payload)) {
      return;
    }

    makeShell(payload);

    /*
     * Existing Jarvis workspace launchers may be installed slightly
     * after DOMContentLoaded. Refresh bindings briefly without
     * rebuilding the shell or changing backend authority.
     */
    let attempts = 0;

    const timer = window.setInterval(() => {
      refreshBindings();

      attempts += 1;

      if (attempts >= 20) {
        window.clearInterval(timer);
      }
    }, 150);

    document.title = "JARVIS — Kali Operations Center";
  }

  if (document.readyState === "loading") {
    document.addEventListener(
      "DOMContentLoaded",
      boot,
      { once: true }
    );
  } else {
    boot();
  }
})();
