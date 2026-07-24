"use strict";

const ENDPOINTS = {
  status: "/operations/status",
  executive: "/operations/executive",
  health: "/operations/health",
  missions: "/operations/missions",
  resources: "/operations/resources",
  timeline: "/operations/timeline?limit=12",
  events: "/operations/events?limit=12",
};

const $ = (id) => document.getElementById(id);
const pick = (...values) => values.find((value) => value !== undefined && value !== null);
const list = (value) => Array.isArray(value) ? value : Array.isArray(value?.items) ? value.items : Array.isArray(value?.entries) ? value.entries : Array.isArray(value?.results) ? value.results : [];
const norm = (value) => String(value || "unknown").toLowerCase().replace(/[^a-z0-9]+/g, "-");
const esc = (value) => String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
const stamp = (value) => {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value || "UNKNOWN") : date.toLocaleString();
};

function pill(element, value) {
  element.className = `pill ${norm(value)}`;
  element.textContent = String(value || "UNKNOWN").toUpperCase();
}

async function get(url) {
  const response = await fetch(url, {cache: "no-store", headers: {Accept: "application/json"}});
  if (!response.ok) throw new Error(`${url}: ${response.status}`);
  return response.json();
}

function connection(ok) {
  $("link").textContent = ok ? "OPERATIONS LINK" : "LINK DEGRADED";
  $("link").className = `pill ${ok ? "connected" : "disconnected"}`;
  $("api").textContent = ok ? "CONNECTED" : "DEGRADED";
}

function renderExecutive(payload) {
  const state = pick(payload.state, payload.status, "unknown");
  const readinessValue = pick(payload.readiness, 0);
  const readiness = typeof readinessValue === "number" ? Math.round(readinessValue <= 1 ? readinessValue * 100 : readinessValue) : 0;

  $("status").textContent = String(state).toUpperCase();
  $("status").className = norm(state);
  $("status-detail").textContent = pick(payload.detail, "Executive telemetry received.");
  $("readiness").textContent = `${readiness}%`;
  $("readiness").parentElement.setAttribute("aria-valuenow", String(readiness));
  $("executive-mission").textContent = pick(payload.active_mission_id, "UNASSIGNED");
  $("executive-objective").textContent = pick(payload.active_objective_id, "UNASSIGNED");
  $("executive-activity").textContent = pick(payload.current_activity, "IDLE");
  $("last-transition").textContent = stamp(payload.last_transition_at);
  $("observations").textContent = pick(payload.observation_count, 0);
  $("inferences").textContent = pick(payload.inference_count, 0);
  $("plans").textContent = pick(payload.plan_count, 0);
  $("pending-decisions").textContent = pick(payload.pending_decisions, 0);
  $("pending-recommendations").textContent = pick(payload.pending_recommendations, 0);
}

function renderStatus(payload) {
  const generated = pick(payload.generated_at, payload.timestamp);
  $("snapshot-time").textContent = generated ? `Snapshot ${stamp(generated)}` : "Operational snapshot received";
  if (payload.executive) renderExecutive(payload.executive);
  renderCards(payload, "alerts", "alerts", "alert-count", "ACTIVE");
}

function renderMissions(payload) {
  const missions = list(payload);
  const activeMission = missions.find((mission) => ["active", "running", "executing", "in-progress"].includes(norm(pick(mission.state, mission.status)))) || missions[0];
  const counts = {active: 0, queued: 0, complete: 0};
  missions.forEach((mission) => {
    const state = norm(pick(mission.state, mission.status));
    if (["active", "running", "executing", "in-progress"].includes(state)) counts.active += 1;
    else if (["complete", "completed", "certified", "done"].includes(state)) counts.complete += 1;
    else counts.queued += 1;
  });
  $("active").textContent = pick(payload.active_count, counts.active);
  $("queued").textContent = pick(payload.queued_count, counts.queued);
  $("complete").textContent = pick(payload.completed_count, payload.complete_count, counts.complete);
  if (!activeMission) {
    pill($("mission-state"), "idle");
    return;
  }
  $("mission").textContent = pick(activeMission.title, activeMission.name, activeMission.mission_id, "Active mission");
  $("objective").textContent = pick(activeMission.objective, activeMission.description, activeMission.summary, "Mission objective not supplied.");
  pill($("mission-state"), pick(activeMission.state, activeMission.status, "active"));
}

function renderHealth(payload) {
  let components = list(payload);
  if (!components.length && payload && typeof payload === "object") {
    components = Object.entries(payload).filter(([, value]) => value && typeof value === "object").map(([name, value]) => ({name, ...value}));
  }
  $("divisions-list").innerHTML = ["operations", "knowledge", "reasoning", "cognition"].map((name) => {
    const component = components.find((item) => norm(pick(item.name, item.component, item.service)) === name);
    const state = pick(component?.state, component?.status, component?.health, "unknown");
    return `<div class="row"><span>${name[0].toUpperCase() + name.slice(1)}</span><span class="pill ${norm(state)}">${esc(String(state).toUpperCase())}</span></div>`;
  }).join("");
}

function renderResources(payload) {
  const resources = list(payload);
  const findResource = (name) => resources.find((item) => norm(pick(item.name, item.kind, item.resource)) === name);
  $("resources-list").innerHTML = ["cpu", "memory", "storage"].map((name) => {
    let value = pick(payload?.[name], payload?.[`${name}_percent`], name === "storage" ? payload?.disk_percent : null, findResource(name));
    if (value && typeof value === "object") value = pick(value.percent, value.utilization, value.used_percent, value.value);
    const percentage = typeof value === "number" ? Math.max(0, Math.min(100, value <= 1 ? value * 100 : value)) : 0;
    return `<div class="resource"><div class="resource-title"><span>${name.toUpperCase()}</span><b>${percentage ? Math.round(percentage) + "%" : "--"}</b></div><div class="meter"><i style="width:${percentage}%"></i></div></div>`;
  }).join("");
}

function renderTimeline(payload) {
  const events = list(payload).slice(0, 12);
  $("event-count").textContent = `${events.length} EVENTS`;
  $("timeline").innerHTML = events.length ? events.map((event) => `<li class="event"><time>${esc(stamp(pick(event.timestamp, event.occurred_at, event.created_at)))}</time><div><b>${esc(pick(event.title, event.name, event.event_kind, event.event_type, event.type, "Operational event"))}</b><p>${esc(pick(event.detail, event.description, event.message, event.summary, ""))}</p></div></li>`).join("") : '<li class="empty">No operational events received.</li>';
}

function renderCards(payload, key, target, count, label) {
  const items = list(payload?.[key]);
  $(count).textContent = `${items.length} ${label}`;
  $(target).innerHTML = items.length ? items.slice(0, 5).map((item) => `<div class="card"><b>${esc(pick(item.title, item.name, key === "alerts" ? item.severity : "Recommendation"))}</b><p>${esc(pick(item.rationale, item.detail, item.description, item.message, item.summary, ""))}</p></div>`).join("") : `No ${key === "alerts" ? "active operational alerts" : "recommendations require authorization"}.`;
}

function renderRecommendations(executive) {
  const pending = Number(pick(executive?.pending_recommendations, 0));
  $("recommendation-count").textContent = `${pending} PENDING`;
  $("recommendations").textContent = pending ? `${pending} executive recommendation${pending === 1 ? "" : "s"} await commander review.` : "No recommendations require authorization.";
}

async function refresh() {
  const button = $("refresh");
  button.disabled = true;
  button.textContent = "Refreshing Operational Picture";
  const pairs = await Promise.all(Object.entries(ENDPOINTS).map(async ([key, url]) => {
    try { return [key, await get(url), null]; }
    catch (error) { return [key, null, error]; }
  }));
  const results = Object.fromEntries(pairs.map(([key, data, error]) => [key, {data, error}]));
  connection(Boolean(results.status.data || results.executive.data));
  if (results.status.data) renderStatus(results.status.data);
  if (results.executive.data) renderExecutive(results.executive.data);
  if (results.missions.data) renderMissions(results.missions.data);
  if (results.health.data) renderHealth(results.health.data);
  if (results.resources.data) renderResources(results.resources.data);
  renderTimeline(results.timeline.data || results.events.data || {});
  renderRecommendations(results.executive.data || results.status.data?.executive || {});
  $("sync").textContent = new Date().toLocaleTimeString();
  button.disabled = false;
  button.textContent = "Refresh Operational Picture";
}

document.addEventListener("DOMContentLoaded", () => {
  setInterval(() => $("clock").textContent = new Date().toLocaleTimeString([], {hour12: false}), 1000);
  $("refresh").addEventListener("click", refresh);
  refresh();
  setInterval(refresh, 15000);
});
