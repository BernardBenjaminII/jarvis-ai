"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const root = process.cwd();
const jsPath = path.join(root, "core/src/static/mission_control/bounty_agent_workspace.js");
const cssPath = path.join(root, "core/src/static/mission_control/bounty_agent_workspace.css");
const js = fs.readFileSync(jsPath, "utf8");
const css = fs.readFileSync(cssPath, "utf8");

function extractBrowser() {
  const start = "  const opportunityBrowserState = {";
  const end = "  // JARVIS_R922D2_OPPORTUNITY_RENDER";
  assert.equal(js.split(start).length - 1, 1, "Exactly one browser state declaration");
  assert.equal(js.split(end).length - 1, 1, "Exactly one legacy render anchor");
  const a = js.indexOf(start);
  const b = js.indexOf(end, a + start.length);
  assert.ok(a >= 0 && b > a, "Browser renderer is before legacy renderer");
  return js.slice(a, b);
}

function makeHarness(api) {
  const selectors = [
    "#jba-oc-content", "#jba-oc-status", "#jba-oc-summary",
    "#jba-oc-page", "#jba-oc-prev", "#jba-oc-next",
  ];
  const nodes = Object.fromEntries(selectors.map(s => [s, {
    isConnected: true,
    textContent: "",
    innerHTML: "",
    disabled: false,
  }]));
  const panel = {querySelector: s => nodes[s] || null};
  const host = {querySelector: s => s === ".jba-opportunity-command"
    ? panel : (nodes[s] || null)};
  const escapeHtml = v => String(v).replace(/&/g, "&amp;")
    .replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  const sandbox = {host, api, esc: escapeHtml, URLSearchParams};
  vm.runInNewContext(extractBrowser() + `
    globalThis.__browserTest = {
      state: opportunityBrowserState,
      load: loadOpportunityBrowser
    };
  `, sandbox, {filename: "R10.0C2 browser renderer"});
  return {...sandbox.__browserTest, nodes};
}

function response(url, overrides = {}) {
  const parsed = new URL(url, "http://127.0.0.1");
  const search = parsed.searchParams.get("search") || "";
  const limit = Number(parsed.searchParams.get("limit"));
  const offset = Number(parsed.searchParams.get("offset"));
  const total = search ? 1 : 52;
  const count = Math.max(0, Math.min(limit, total - offset));
  const results = Array.from({length: count}, (_, n) => {
    const i = offset + n + 1;
    return {
      program: search ? "Newegg <img src=x onerror=alert(1)>" : `Program ${i}`,
      platform: "hackerone",
      source: search ? "manual_policy_import" : "hackerone_api_snapshot",
      source_identifier: `id-${i}`,
      review_lane: search ? "IMPORTED_POLICY" : "MANUAL_A",
      next_action: "Review official policy",
      human_review_required: true,
      testing_authorized: false,
      execution_enabled: false,
      automatic_execution_ready: false,
      submission_authorized: false,
      existing_manual_viability_score: 60,
    };
  });
  return {
    schema: "jarvis.bounty.opportunity_browser.r10c1",
    mode: "offline_read_only",
    network_requests: 0,
    human_review_required: true,
    testing_authorized: false,
    automatic_execution_allowed: false,
    mission_creation_allowed: false,
    submission_authorized: false,
    limit,
    offset,
    total_opportunities: 52,
    total_matched: total,
    returned_count: count,
    has_more: offset + count < total,
    catalog_status: "fresh",
    results,
    ...overrides,
  };
}

test("Command Center is wired and original panel retained", () => {
  assert.match(js, /JARVIS_R100C2_COMMAND_CENTER/);
  assert.match(css, /JARVIS_R100C2_COMMAND_CENTER/);
  assert.match(js, /JARVIS_R922D2_OPPORTUNITY_PANEL/);
  for (const control of ["#jba-oc-form", "#jba-oc-reset", "#jba-oc-prev", "#jba-oc-next"]) {
    assert.ok(js.includes(control), `Missing control ${control}`);
  }
  assert.match(js, /void loadOpportunityBrowser\(\)/);
});

test("Pages 25 records and updates Previous/Next controls", async () => {
  const calls = [];
  const browser = makeHarness(async url => {
    calls.push(new URL(url, "http://127.0.0.1"));
    return response(url);
  });
  await browser.load();
  assert.equal(calls[0].pathname, "/api/bounty-agent/opportunities");
  assert.equal(calls[0].searchParams.get("limit"), "25");
  assert.match(browser.nodes["#jba-oc-summary"].textContent, /Showing 1–25 of 52/);
  assert.equal(browser.nodes["#jba-oc-page"].textContent, "Page 1 of 3");
  assert.equal(browser.nodes["#jba-oc-prev"].disabled, true);
  assert.equal(browser.nodes["#jba-oc-next"].disabled, false);

  browser.state.offset = 25;
  await browser.load();
  assert.match(browser.nodes["#jba-oc-summary"].textContent, /Showing 26–50 of 52/);
  assert.equal(browser.nodes["#jba-oc-prev"].disabled, false);
  assert.equal(browser.nodes["#jba-oc-next"].disabled, false);

  browser.state.offset = 50;
  await browser.load();
  assert.match(browser.nodes["#jba-oc-summary"].textContent, /Showing 51–52 of 52/);
  assert.equal(browser.nodes["#jba-oc-page"].textContent, "Page 3 of 3");
  assert.equal(browser.nodes["#jba-oc-next"].disabled, true);
});

test("Search/filter request encodes values and escapes program HTML", async () => {
  let captured;
  const browser = makeHarness(async url => {
    captured = new URL(url, "http://127.0.0.1");
    return response(url);
  });
  browser.state.search = "Newegg & <test>";
  browser.state.source = "manual_policy_import";
  browser.state.lane = "IMPORTED_POLICY";
  await browser.load();
  assert.equal(captured.searchParams.get("search"), "Newegg & <test>");
  assert.equal(captured.searchParams.get("source"), "manual_policy_import");
  assert.equal(captured.searchParams.get("lane"), "IMPORTED_POLICY");
  assert.equal(browser.nodes["#jba-oc-status"].textContent, "1 matches");
  assert.match(browser.nodes["#jba-oc-content"].innerHTML, /Newegg &lt;img/);
  assert.doesNotMatch(browser.nodes["#jba-oc-content"].innerHTML, /<img/);
});

test("Unsafe response fails closed without rendering opportunity cards", async () => {
  const browser = makeHarness(async url => response(url, {testing_authorized: true}));
  await browser.load();
  assert.equal(browser.nodes["#jba-oc-status"].textContent, "Unavailable");
  assert.match(browser.nodes["#jba-oc-content"].textContent, /Unsafe opportunity browser response/);
  assert.equal(browser.nodes["#jba-oc-next"].disabled, true);
});

test("Out-of-order responses cannot replace a newer page", async () => {
  const waiting = [];
  const browser = makeHarness(url => new Promise(resolve => waiting.push({url, resolve})));
  const first = browser.load();
  browser.state.offset = 25;
  const second = browser.load();
  assert.equal(waiting.length, 2);
  waiting[1].resolve(response(waiting[1].url));
  await second;
  assert.match(browser.nodes["#jba-oc-summary"].textContent, /Showing 26–50 of 52/);
  waiting[0].resolve(response(waiting[0].url));
  await first;
  assert.match(browser.nodes["#jba-oc-summary"].textContent, /Showing 26–50 of 52/);
});
