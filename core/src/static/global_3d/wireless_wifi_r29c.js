// JARVIS_WIFI_R29C_DASHBOARD
(() => {
  "use strict";

  const $ = id => document.getElementById(id);
  let networks = [];
  let loading = false;
  let selected = null;

  function el(tag, value, className) {
    const node = document.createElement(tag);
    if (value !== undefined && value !== null) {
      node.textContent = String(value);
    }
    if (className) node.className = className;
    return node;
  }

  function formatTime(value) {
    if (!value) return "Unknown";
    const date = new Date(value);
    return Number.isNaN(date.getTime())
      ? "Unknown"
      : date.toLocaleString();
  }

  // JARVIS_WIFI_R29E1_SSID_DISPLAY
  function networkName(n) {
    const raw = n.ssid_hex || "";

    if (!raw) return "Empty / unknown SSID";

    // Decode the original bytes strictly. The decoder's
    // replacement characters must not become network names.
    try {
      const bytes = raw.match(/.{2}/g) || [];
      const data = Uint8Array.from(
        bytes.map(v => parseInt(v, 16))
      );

      const text = new TextDecoder(
        "utf-8", {fatal: true}
      ).decode(data);

      if (!text.trim() || /[\x00-\x1f\x7f]/.test(text)) {
        return "Undecodable SSID";
      }

      return text;
    } catch (_) {
      return "Undecodable SSID";
    }
  }


  // JARVIS_WIFI_R29E_FRESHNESS
  function freshness(value) {
    const timestamp = Date.parse(value || "");
    if (!Number.isFinite(timestamp)) {
      return {label: "Unknown", kind: "unknown"};
    }

    const age = Math.max(0, Date.now() - timestamp);

    if (age < 10 * 60 * 1000) {
      return {label: "Recently observed", kind: "recent"};
    }
    if (age < 60 * 60 * 1000) {
      return {label: "Stale", kind: "stale"};
    }
    return {label: "Historical", kind: "historical"};
  }

  function authenticationLabel(suite) {
    const names = {
      "000fac01": "802.1X / EAP",
      "000fac02": "WPA2-PSK",
      "000fac03": "FT-802.1X",
      "000fac04": "FT-PSK",
      "000fac08": "WPA3-SAE",
      "000fac09": "FT-SAE",
      "000fac12": "OWE"
    };
    const key = String(suite).toLowerCase();
    return names[key] || "Unknown AKM (" + suite + ")";
  }

  function field(parent, label, value) {
    const box = el("div", null, "wifi-field");
    box.append(
      el("span", label),
      el("strong", value ?? "Unknown")
    );
    parent.append(box);
  }

  function showDetail(n) {
    selected = {
      sensor_id: n.sensor_id,
      bssid: n.bssid
    };

    $("wifiDetail").hidden = false;
    $("wifiDetailTitle").textContent = networkName(n);

    const body = $("wifiDetailBody");
    body.replaceChildren();

    const grid = el("div", null, "wifi-detail-grid");

    field(grid, "BSSID", n.bssid);
    field(grid, "Sensor", n.sensor_id);
    field(grid, "Channel (advertised)", n.channel_ie);
    field(
      grid,
      "Last measured RSSI",
      n.signal_dbm == null ? "Unknown" : n.signal_dbm + " dBm"
    );
    field(grid, "Security advertised", n.security);
    field(grid, "Observation status", freshness(n.last_seen).label);
    field(grid, "Frames recorded", n.frames_seen);
    field(grid, "First observed", formatTime(n.first_seen));
    field(grid, "Last observed", formatTime(n.last_seen));
    field(grid, "SSID raw bytes", n.ssid_hex || "(empty)");

    let akms = [];
    try {
      const parsed = JSON.parse(n.akms_json || "[]");
      if (Array.isArray(parsed)) akms = parsed;
    } catch (_) {}

    field(
      grid,
      "Authentication suite identifiers",
      akms.length
        ? akms.map(authenticationLabel).join(", ")
        : "None decoded"
    );

    body.append(grid);

    body.append(el(
      "p",
      "Identification limits: This is a stored access-point " +
      "observation, not a live availability check. A BSSID does " +
      "not necessarily correspond to a separate physical router. " +
      "An empty SSID does not prove the network is intentionally " +
      "hidden. Security fields describe advertised capabilities.",
      "wifi-caution"
    ));

    $("wifiDetail").scrollIntoView({
      behavior: "smooth",
      block: "nearest"
    });
  }

  function render() {
    const query = $("wifiSearch").value.trim().toLowerCase();
    const body = $("wifiRows");
    body.replaceChildren();

    const filtered = networks.filter(n =>
      [
        n.ssid_display,
        n.ssid_hex,
        n.bssid,
        n.sensor_id,
        n.security,
        String(n.channel_ie ?? "")
      ].some(v => String(v ?? "").toLowerCase().includes(query))
    );

    if (!filtered.length) {
      const row = el("tr");
      const cell = el(
        "td",
        networks.length
          ? "No matching Wi-Fi networks."
          : "No Wi-Fi networks stored."
      );
      cell.colSpan = 8;
      row.append(cell);
      body.append(row);
      return;
    }

    for (const n of filtered) {
      const row = el("tr");
      row.className = "wifi-network-row";
      row.tabIndex = 0;
      row.setAttribute("role", "button");
      row.setAttribute("aria-label",
        "Inspect network " + networkName(n));

      const values = [
        networkName(n),
        n.bssid,
        n.sensor_id,
        n.channel_ie ?? "—",
        n.signal_dbm == null ? "—" : n.signal_dbm + " dBm",
        n.security ?? "Unknown",
        formatTime(n.last_seen)
      ];

      for (const value of values) {
        row.append(el("td", value));
      }

      const status = freshness(n.last_seen);
      const statusCell = el("td");
      statusCell.append(
        el(
          "span",
          status.label,
          "wifi-status wifi-status-" + status.kind
        )
      );
      row.append(statusCell);

      row.addEventListener("click", () => showDetail(n));
      row.addEventListener("keydown", event => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          showDetail(n);
        }
      });
      body.append(row);
    }
  }

  async function refresh() {
    if (loading) return;
    loading = true;
    $("wifiRefresh").disabled = true;

    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 7000);
      let response;

      try {
        response = await fetch(
          "/api/sensors/wifi/networks",
          {cache: "no-store", signal: controller.signal}
        );
      } finally {
        clearTimeout(timer);
      }

      if (!response.ok) {
        throw new Error("HTTP " + response.status);
      }

      const data = await response.json();
      if (!data.available || !Array.isArray(data.networks)) {
        throw new Error("Stored Wi-Fi inventory unavailable");
      }

      networks = data.networks;

      const sensors = new Set(
        networks.map(n => n.sensor_id)
      );

      const mostRecent = networks
        .map(n => Date.parse(n.last_seen || ""))
        .filter(Number.isFinite);

      const newest = mostRecent.length
        ? new Date(Math.max(...mostRecent)).toLocaleString()
        : "Unknown";

      $("wifiSummary").textContent =
        `${networks.length} stored BSSIDs · ` +
        `${sensors.size} sensors · ` +
        `Latest observation: ${newest}`;

      $("wifiUpdated").textContent =
        "Inventory loaded " + new Date().toLocaleTimeString() +
        " · Radio captures run separately on a system timer";

      render();

      if (selected) {
        const match = networks.find(n =>
          n.sensor_id === selected.sensor_id &&
          n.bssid === selected.bssid
        );

        if (match && !$("wifiDetail").hidden) {
          // Refresh details without shifting scroll position.
          const position = window.scrollY;
          showDetail(match);
          window.scrollTo({top: position});
        }
      }
    } catch (error) {
      $("wifiSummary").textContent =
        "Wi-Fi inventory error: " + error.message;
    } finally {
      loading = false;
      $("wifiRefresh").disabled = false;
    }
  }

  $("wifiSearch").addEventListener("input", render);
  $("wifiRefresh").addEventListener("click", refresh);

  $("wifiDetailClose").addEventListener("click", () => {
    selected = null;
    $("wifiDetail").hidden = true;
  });

  refresh();
  setInterval(refresh, 30000);
})();
