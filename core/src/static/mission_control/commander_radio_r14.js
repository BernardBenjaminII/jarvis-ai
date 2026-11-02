(() => {
  "use strict";

  const API = "/api/radio";
  const SERIAL = "05370246";
  let presets = [];
  let working = false;
  let status = {};

  const request = async (path, method = "GET", body = null) => {
    const response = await fetch(API + path, {
      method,
      cache: "no-store",
      headers: {"Content-Type": "application/json"},
      ...(body ? {body: JSON.stringify(body)} : {})
    });

    const data = await response.json();

    if (!response.ok)
      throw new Error(data.detail || `HTTP ${response.status}`);

    return data;
  };

  const $ = selector =>
    document.querySelector("#jarvis-radio " + selector);

  function notice(text) {
    const element = $(".radio-message");
    if (element) element.textContent = text;
  }

  async function refresh() {
    if (working || !$("#jarvis-radio-status")) return;

    try {
      const result = await request("/status");
      if (result.serial !== SERIAL)
        throw new Error("Receiver identity mismatch");

      status = result.status;
      const running = status.state === "running";
      const fm = running && status.task === "fm";

      $("#jarvis-radio-status").textContent =
        running ? (fm ? "FM ACTIVE" : "SDR-B BUSY") :
        status.state === "idle" ? "READY" : status.state;

      $(".radio-frequency").textContent =
        fm ? (status.frequency_hz / 1e6).toFixed(1) + " MHz" :
        "--.- MHz";

      $(".radio-station").textContent =
        fm
          ? (presets.find(p =>
              p.frequency_hz === status.frequency_hz
            )?.name || "Manual FM")
          : "No station selected";

      $(".radio-stop").disabled = !fm;

      document.querySelectorAll("#jarvis-radio [data-preset]")
        .forEach(button => {
          const preset = presets.find(p =>
            p.id === button.dataset.preset
          );

          button.classList.toggle(
            "selected",
            fm && preset?.frequency_hz === status.frequency_hz
          );

          button.disabled = running && !fm;
        });

    } catch (error) {
      $("#jarvis-radio-status").textContent = "OFFLINE";
      notice(error.message);
    }
  }

  async function tune(id) {
    if (working) return;
    working = true;

    try {
      const preset = presets.find(p => p.id === id);
      if (!preset) throw new Error("Unknown station");

      const current = (await request("/status")).status;

      if (current.state !== "idle") {
        if (current.state !== "running" || current.task !== "fm")
          throw new Error("SDR-B is occupied by another mission");

        if (current.frequency_hz === preset.frequency_hz) {
          notice("Station already selected");
          return;
        }

        if (!confirm(`Switch to ${preset.name}?`)) return;

        await request("/stop", "POST");
      }

      await request("/tune", "POST", {preset_id: id});
      notice(`${preset.name} selected · Audio on Xperion`);

    } catch (error) {
      notice("Radio: " + error.message);
    } finally {
      working = false;
      await refresh();
    }
  }

  async function stop() {
    if (working) return;
    working = true;

    try {
      await request("/stop", "POST");
      notice("Radio stopped");
    } catch (error) {
      notice(error.message);
    } finally {
      working = false;
      await refresh();
    }
  }

  async function mount() {
    if (document.getElementById("jarvis-radio")) return;

    const heading = document.getElementById(
      "commander-brief-heading"
    );

    if (!heading) return;

    const section = document.createElement("section");
    section.id = "jarvis-radio";
    section.innerHTML = `
      <div class="radio-top">
        <h3>COMMUNICATIONS · LOCAL RADIO</h3>
        <span id="jarvis-radio-status">CONNECTING</span>
      </div>
      <div class="radio-display">
        <div class="radio-station">No station selected</div>
        <div class="radio-frequency">--.- MHz</div>
        <small>SDR-B · Local audio output</small>
      </div>
      <div class="radio-buttons"></div>
      <button class="radio-stop" disabled>STOP RADIO</button>
      <p class="radio-message" role="status">Loading presets...</p>
    `;

    const shell = document.getElementById("jarvis-r32-shell");
    const operations = document.getElementById("jarvis-r32-operations");

    if (!shell || !operations || operations.parentElement !== shell) {
      console.warn("[JARVIS Radio] Executive shell not ready");
      return;
    }

    shell.insertBefore(section, shell.firstElementChild);

    section.querySelector(".radio-stop").onclick = stop;

    try {
      const data = await request("/presets");

      if (data.receiver_serial !== SERIAL)
        throw new Error("Wrong preset receiver");

      presets = data.presets.filter(
        p => p.modulation === "fm" &&
        Number.isInteger(p.frequency_hz) &&
        p.frequency_hz >= 87500000 &&
        p.frequency_hz <= 108000000
      );

      const buttons = section.querySelector(".radio-buttons");

      for (const preset of presets) {
        const button = document.createElement("button");
        button.dataset.preset = preset.id;
        button.textContent =
          `${preset.name} · ${(preset.frequency_hz / 1e6).toFixed(1)}`;
        button.onclick = () => tune(preset.id);
        buttons.appendChild(button);
      }

      notice(`${presets.length} presets loaded`);
      await refresh();
      setInterval(refresh, 5000);

    } catch (error) {
      notice("Initialization failed: " + error.message);
    }
  }

  // R1.7B: Retry mounting while Executive Shell initializes.
  function initializeRadio() {
    let attempts = 0;

    const retry = () => {
      if (document.getElementById("jarvis-radio")) {
        return true;
      }

      const shell = document.getElementById("jarvis-r32-shell");
      const operations = document.getElementById(
        "jarvis-r32-operations"
      );

      if (
        shell &&
        operations &&
        operations.parentElement === shell
      ) {
        mount();
      }

      return !!document.getElementById("jarvis-radio");
    };

    if (retry()) return;

    const timer = window.setInterval(() => {
      attempts++;

      if (retry() || attempts >= 60) {
        window.clearInterval(timer);
      }

      if (attempts >= 60 &&
          !document.getElementById("jarvis-radio")) {
        console.warn(
          "[JARVIS Radio] Executive workspace unavailable"
        );
      }
    }, 1000);
  }

  if (document.readyState === "loading") {
    document.addEventListener(
      "DOMContentLoaded",
      initializeRadio,
      {once: true}
    );
  } else {
    initializeRadio();
  }
})();
