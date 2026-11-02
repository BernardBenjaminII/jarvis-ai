// JARVIS_WIRELESS_R27A_FRONTEND
(() => {
  "use strict";

  const base = "/api/sensors/";
  const $ = id => document.getElementById(id);
  let devices = [];
  let fetching = false;

  async function get(path) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 7000);
    try {
      const response = await fetch(base + path, {
        cache: "no-store", signal: controller.signal
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } finally {
      clearTimeout(timeout);
    }
  }

  function setState(id, state, detail) {
    const node = $(id + "State");
    node.textContent = String(state || "unknown").toUpperCase();
    node.className = "state " + String(state || "offline").toLowerCase();
    $(id + "Detail").textContent = detail;
  }

  function wifiInventory(data) {
    if (Array.isArray(data)) return data;
    if (!data || typeof data !== "object") return [];
    if (Array.isArray(data.sensors)) return data.sensors;
    if (data.sensors && typeof data.sensors === "object") {
      return Object.entries(data.sensors).map(([id, value]) => ({
        sensor_id: id, ...(value || {})
      }));
    }
    return Object.entries(data)
      .filter(([key]) => /^wifi-0[12]$/i.test(key))
      .map(([id, value]) => ({sensor_id: id, ...(value || {})}));
  }

  function renderRows() {
    const search = $("search").value.trim().toLowerCase();
    const rows = devices.filter(d =>
      [
      d.address,
      d.advertised_name,
      d.manufacturer,
      d.company_id_hex,
      String(d.address_type)
    ]
        .some(value => String(value ?? "").toLowerCase().includes(search))
    );

    const body = $("deviceRows");
    body.replaceChildren();

    if (!rows.length) {
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.colSpan = 7;
      td.textContent = "No matching recent BLE observations";
      tr.append(td);
      body.append(tr);
      return;
    }

    for (const d of rows) {
      const tr = document.createElement("tr");
      const cells = [
        d.advertised_name || "Unnamed",
        d.address || "—",
        d.manufacturer
          ? d.manufacturer +
            (d.company_id_hex ? " (" + d.company_id_hex + ")" : "")
          : "Unknown",
        d.address_type === 0 ? "Public" :
          d.address_type === 1 ? "Random" :
          String(d.address_type ?? "—"),
        d.avg_rssi == null ? "—" : d.avg_rssi + " dBm",
        d.sightings ?? "—",
        d.last_seen ? new Date(d.last_seen).toLocaleTimeString() : "—"
      ];

      cells.forEach((value, index) => {
        const td = document.createElement("td");
        td.textContent = String(value);
        if (index === 1) td.className = "address";
        tr.append(td);
      });
      body.append(tr);
    }
  }

  async function refresh() {
    if (fetching) return;
    fetching = true;
    try {
      const minutes = Number($("window").value);
      const paths = [
        "iot/status", "iot/summary",
        `iot/devices?minutes=${minutes}&limit=500`, "wifi/status"
      ];
      const results = await Promise.allSettled(paths.map(get));
      const value = i => results[i].status === "fulfilled"
        ? results[i].value : null;

      const health = value(0);
      const summary = value(1);
      const inventory = value(2);
      const wifi = value(3);

      setState("iot", health?.state || "offline",
        `Firmware ${health?.firmware || "—"} · Heartbeat ${
          health?.age_seconds ?? "—"}s ago`);

      const adapters = wifiInventory(wifi);
      for (const [name, id] of [
        ["WIFI-01", "wifi1"], ["WIFI-02", "wifi2"]
      ]) {
        const adapter = adapters.find(a =>
          String(a.sensor_id || a.id || a.name || "").toUpperCase() === name);
        setState(id, adapter?.state || adapter?.status ||
          (adapter?.ready ? "ready" : "offline"),
          adapter?.interface || adapter?.iface || "Inventory unavailable");
      }

      $("count").textContent = summary?.observations ?? "—";
      $("addresses").textContent = summary?.distinct_addresses ?? "—";
      $("rssi").textContent = summary?.avg_rssi == null
        ? "—" : summary.avg_rssi + " dBm";

      if (inventory && Array.isArray(inventory.devices)) {
        devices = inventory.devices;
      } else {
        devices = [];
      }
      $("recent").textContent = devices.length;
      renderRows();

      $("updated").textContent = "Passive observation · Last refreshed " +
        new Date().toLocaleTimeString();
    } catch (error) {
      $("updated").textContent = "Refresh error: " + error.message;
    } finally {
      fetching = false;
    }
  }

  $("search").addEventListener("input", renderRows);
  $("window").addEventListener("change", refresh);
  refresh();
  setInterval(refresh, 15000);
})();
