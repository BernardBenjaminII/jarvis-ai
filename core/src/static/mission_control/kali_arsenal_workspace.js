(() => {
  "use strict";

  const ENDPOINT = "/api/kali/arsenal";

  const esc = (value) =>
    String(value ?? "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    }[c]));

  async function fetchArsenal() {
    const response = await fetch(ENDPOINT, {
      headers: {
        Accept: "application/json",
      },
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(
        `Kali arsenal endpoint returned ${response.status}`
      );
    }

    return response.json();
  }

  function groupBy(items, key) {
    return items.reduce((acc, item) => {
      const value = item[key] || "other";

      if (!acc[value]) acc[value] = [];
      acc[value].push(item);

      return acc;
    }, {});
  }

  function renderCapability(capability) {
    const providers =
      capability.available_providers?.length
        ? capability.available_providers.join(", ")
        : "none";

    return `
      <article class="jka-capability ${capability.available ? "available" : "missing"}">
        <div class="jka-capability-status">
          ${capability.available ? "✓" : "×"}
        </div>
        <div>
          <strong>${esc(capability.label)}</strong>
          <small>${esc(capability.description || "")}</small>
        </div>
        <code>${esc(providers)}</code>
      </article>
    `;
  }

  function renderTool(tool) {
    const marker =
      tool.available
        ? "✓"
        : tool.present
          ? "?"
          : "×";

    const state =
      tool.available
        ? "available"
        : tool.present
          ? "unverified"
          : "missing";

    return `
      <article class="jka-tool ${state}">
        <div class="jka-tool-head">
          <span class="jka-tool-status">${marker}</span>
          <strong>${esc(tool.label)}</strong>
        </div>

        <small>
          ${esc(tool.description || "")}
        </small>

        <code>
          ${esc(tool.path || "not installed")}
        </code>
      </article>
    `;
  }

  function renderToolGroups(tools) {
    const groups = groupBy(tools, "category");

    const order = [
      "discovery",
      "network",
      "web",
      "analysis",
      "intelligence",
    ];

    return order
      .filter((category) => groups[category]?.length)
      .map((category) => `
        <section class="jka-tool-group">
          <h3>${esc(category.toUpperCase())}</h3>

          <div class="jka-tool-grid">
            ${groups[category]
              .map(renderTool)
              .join("")}
          </div>
        </section>
      `)
      .join("");
  }

  async function render(host) {
    host.innerHTML = `
      <button
        class="jarvis-workspace-close"
        type="button"
      >
        ← Return to chat
      </button>

      <main class="jarvis-kali-arsenal">
        <header class="jka-header">
          <div>
            <small>KALI · STATIC CAPABILITY INVENTORY</small>
            <h1>Arsenal</h1>
          </div>

          <button
            id="jka-refresh"
            type="button"
          >
            Refresh
          </button>
        </header>

        <section
          id="jka-body"
          class="jka-loading"
        >
          Inspecting local Kali capabilities…
        </section>
      </main>
    `;

    const body = host.querySelector("#jka-body");
    const refresh = host.querySelector("#jka-refresh");
    const close = host.querySelector(".jarvis-workspace-close");

    close?.addEventListener("click", () => {
      if (window.JARVIS_WORKSPACES?.close) {
        window.JARVIS_WORKSPACES.close();
      }
    });

    async function load() {
      body.className = "jka-loading";
      body.textContent =
        "Inspecting local Kali capabilities…";

      let data;

      try {
        data = await fetchArsenal();
      } catch (error) {
        body.className = "jka-error";

        body.innerHTML = `
          <strong>Arsenal unavailable</strong>
          <p>${esc(error.message)}</p>
        `;

        return;
      }

      const summary = data.summary || {};

      body.className = "";

      body.innerHTML = `
        <section class="jka-summary">
          <article>
            <small>HEALTH</small>
            <strong>
              ${esc(
                String(data.health || "unknown").toUpperCase()
              )}
            </strong>
          </article>

          <article>
            <small>TOOLS AVAILABLE</small>
            <strong>
              ${esc(summary.available_tools ?? 0)}
              /
              ${esc(summary.defined_tools ?? 0)}
            </strong>
          </article>

          <article>
            <small>CAPABILITIES</small>
            <strong>
              ${esc(summary.available_capabilities ?? 0)}
              /
              ${esc(summary.defined_capabilities ?? 0)}
            </strong>
          </article>

          <article>
            <small>MODE</small>
            <strong>STATIC</strong>
          </article>
        </section>

        <section class="jka-section">
          <div class="jka-section-head">
            <div>
              <small>DERIVED FROM INSTALLED TOOLS</small>
              <h2>Capabilities</h2>
            </div>

            <span>
              ${
                summary.missing_required_tools?.length
                  ? `${summary.missing_required_tools.length} required missing`
                  : "All required capabilities available"
              }
            </span>
          </div>

          <div class="jka-capability-list">
            ${(data.capabilities || [])
              .map(renderCapability)
              .join("")}
          </div>
        </section>

        <section class="jka-section">
          <div class="jka-section-head">
            <div>
              <small>LOCAL KALI NODE</small>
              <h2>Tools</h2>
            </div>

            <span>
              ${esc(summary.installed_tools ?? 0)} installed
            </span>
          </div>

          ${renderToolGroups(data.tools || [])}
        </section>
      `;
    }

    refresh.addEventListener("click", load);

    await load();
  }

  window.JarvisKaliArsenalWorkspace = {
    render,
  };
})();
