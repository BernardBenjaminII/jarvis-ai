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


    // JARVIS_EXTERNAL_ARSENAL_R1
    const originalLoad = load;

    async function loadWithExternal() {
      await originalLoad();

      // Do not attach a panel if the inventory failed.
      if (body.classList.contains("jka-error")) return;

      const section = document.createElement("section");
      section.className = "jka-section";
      section.innerHTML = `
        <div class="jka-section-head">
          <div>
            <small>EXTERNAL REFERENCE LIBRARIES</small>
            <h2>Payload Arsenal</h2>
          </div>
          <span id="jka-external-state">Checking…</span>
        </div>
        <p id="jka-external-libraries"></p>
        <form id="jka-external-form">
          <input id="jka-external-query"
            type="search"
            maxlength="100"
            placeholder="Search SQL, XSS, SSRF, admin…"
            aria-label="Search payload reference filenames"
            required />
          <button type="submit">Search references</button>
        </form>
        <div id="jka-external-results"
          aria-live="polite"></div>
      `;

      body.appendChild(section);

      const state = section.querySelector(
        "#jka-external-state"
      );
      const libraries = section.querySelector(
        "#jka-external-libraries"
      );
      const form = section.querySelector(
        "#jka-external-form"
      );
      const query = section.querySelector(
        "#jka-external-query"
      );
      const results = section.querySelector(
        "#jka-external-results"
      );

      let ready = false;

      try {
        const response = await fetch(
          "/api/kali/arsenal/external",
          {cache: "no-store", credentials: "same-origin"}
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        ready = data.state === "ready";

        state.textContent = String(
          data.state || "unknown"
        ).toUpperCase();

        libraries.textContent = (
          data.libraries || []
        ).map((item) =>
          `${item.id}: ${item.available ? "available" : "missing"}`
        ).join(" | ");

      } catch (error) {
        state.textContent = "UNAVAILABLE";
        libraries.textContent = String(error.message);
      }

      query.disabled = !ready;
      form.querySelector("button").disabled = !ready;

      form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const term = query.value.trim();
        if (!term || !ready) return;

        results.textContent = "Searching references…";

        try {
          const url =
            "/api/kali/arsenal/external/search?q=" +
            encodeURIComponent(term) + "&limit=30";

          const response = await fetch(url, {
            cache: "no-store",
            credentials: "same-origin"
          });

          if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
          }

          const data = await response.json();

          if (data.state !== "ready") {
            results.textContent =
              "External arsenal is no longer available.";
            return;
          }

          const entries = data.results || [];

          if (!entries.length) {
            results.textContent = "No matching filenames.";
            return;
          }

          results.innerHTML = `
            <p>${entries.length} matching references
            ${data.truncated ? "(more may exist)" : ""}</p>
            <div class="jka-capability-list">
              ${entries.map((item) => `
                <article class="jka-capability available">
                  <div>
                    <strong>${esc(item.name)}</strong>
                    <small>${esc(item.library)}</small>
                    <code>${esc(item.path)}</code>
                  </div>
                </article>
              `).join("")}
            </div>
          `;

        } catch (error) {
          results.textContent =
            "Search failed: " + String(error.message);
        }
      });
    }

    load = loadWithExternal;


    // JARVIS_WORKSTATION_READINESS_R919R4
    const previousLoad = load;

    load = async function loadWithWorkstation() {
      await previousLoad();

      if (body.classList.contains("jka-error")) return;

      const panel = document.createElement("section");
      panel.className = "jka-section";

      panel.innerHTML = `
        <div class="jka-section-head">
          <div>
            <small>LIVE WORKSTATION INVENTORY</small>
            <h2>Workstation Readiness</h2>
          </div>
          <span id="jka-workstation-state">Checking…</span>
        </div>
        <div id="jka-workstation-content"
             aria-live="polite">Loading…</div>
      `;

      body.appendChild(panel);

      const state = panel.querySelector(
        "#jka-workstation-state"
      );
      const content = panel.querySelector(
        "#jka-workstation-content"
      );

      try {
        const response = await fetch(
          "/api/kali/arsenal/workstation",
          {
            cache: "no-store",
            credentials: "same-origin",
            headers: { Accept: "application/json" }
          }
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (!data || !data.tools || !data.arsenal) {
          throw new Error("Invalid inventory response");
        }

        const libraries = Array.isArray(
          data.arsenal.libraries
        ) ? data.arsenal.libraries : [];

        const readyLibraries = libraries.filter(
          item => item.available === true
        ).length;

        state.textContent = String(
          data.state || "unknown"
        ).toUpperCase();

        const toolRows = Object.entries(data.tools)
          .map(([name, tool]) => `
            <article class="jka-capability">
              <div class="jka-capability-status">
                ${tool.installed ? "✓" : "×"}
              </div>
              <div>
                <strong>${esc(name)}</strong>
                <small>
                  ${tool.installed ? "Installed" : "Missing"}
                </small>
              </div>
              <code>${esc(tool.path || "—")}</code>
            </article>
          `).join("");

        content.innerHTML = `
          <section class="jka-summary">
            <article>
              <small>INSTALLED TOOLS</small>
              <strong>${esc(data.installed_count)} /
                ${esc(data.tool_count)}</strong>
            </article>
            <article>
              <small>ARSENAL LIBRARIES</small>
              <strong>${readyLibraries} /
                ${libraries.length}</strong>
            </article>
            <article>
              <small>ARSENAL STATE</small>
              <strong>${esc(data.arsenal.state)}</strong>
            </article>
            <article>
              <small>EXECUTION</small>
              <strong>
                ${data.execution_authorized === true
                  ? "AUTHORIZED"
                  : "LOCKED"}
              </strong>
            </article>
          </section>
          <p>
            Inventory only. Tool installation does not
            authorize target scanning or payload execution.
          </p>
          <div class="jka-capability-list">
            ${toolRows}
          </div>
        `;
      } catch (error) {
        state.textContent = "UNAVAILABLE";
        content.textContent =
          "Live inventory unavailable: " + error.message;
      }
    };

    refresh.addEventListener("click", load);

    await load();
  }

  window.JarvisKaliArsenalWorkspace = {
    render,
  };
})();
