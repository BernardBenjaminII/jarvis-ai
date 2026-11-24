"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const js = fs.readFileSync("core/src/static/mission_control/bounty_agent_workspace.js", "utf8");
const css = fs.readFileSync("core/src/static/mission_control/bounty_agent_workspace.css", "utf8");
function implementation() {
  const start = "  const opportunityReviewState = {";
  const end = "  // JARVIS_R922D2_OPPORTUNITY_RENDER";
  assert.equal(js.split(start).length - 1, 1);
  assert.equal(js.split(end).length - 1, 1);
  const a = js.indexOf(start);
  const b = js.indexOf(end, a);
  assert.ok(a >= 0 && b > a);
  return js.slice(a, b);
}
function fixture(n = 1, overrides = {}) {
  const records = Array.from({length: n}, (_, i) => ({
    id: i + 1,
    program: i ? `Program ${i + 1}` : "GCash <img src=x onerror=alert(1)>",
    handle: i ? `handle-${i + 1}` : "gcash_vdp",
    run_id: "synthetic-complete-run",
    previous_run_id: "synthetic-baseline",
    event_type: i ? "listing_changed" : "new_listing",
    review_state: "pending",
    changed_fields: i ? ["policy_sha256"] : [],
    human_review_required: true,
    testing_authorized: false,
  }));
  return {
    schema: "jarvis.bounty.review_queue.r10b",
    network_requests: 0,
    human_review_only: true,
    testing_authorized: false,
    execution_authorized: false,
    submission_authorized: false,
    notification_authorized: false,
    alerts_issued: 0,
    status: "ready",
    limit: 10,
    offset: 0,
    total_events: n,
    counts: {pending:n, acknowledged:0, deferred:0, resolved:0},
    records: records.slice(0, 10),
    ...overrides,
  };
}
function harness(api, {confirmed = true} = {}) {
  const selectors = ["#jba-or-records", "#jba-or-status", "#jba-or-counts",
    "#jba-or-page", "#jba-or-prev", "#jba-or-next"];
  const nodes = Object.fromEntries(selectors.map(key => [key, {
    textContent:"", innerHTML:"", isConnected:true, disabled:false,
  }]));
  const historyNode = {textContent:"", innerHTML:"", isConnected:true};
  const panel = {
    isConnected:true,
    querySelector: key => nodes[key] ||
      (/^\[data-review-history="\d+"\]$/.test(key) ? historyNode : null),
  };
  const host = {querySelector: key => key === ".jba-opportunity-reviews" ? panel :
    (nodes[key] || (/^\[data-review-history="\d+"\]$/.test(key) ? historyNode : null))};
  const esc = value => String(value ?? "").replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;").replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;").replaceAll("'", "&#39;");
  let confirms = 0;
  const context = {
    host, api, esc, URLSearchParams,
    window: {confirm: () => { confirms++; return confirmed; }},
    crypto: {randomUUID: () => "18b523ad-2327-4635-a7e0-000000000001"},
  };
  vm.runInNewContext(implementation() + `
    globalThis.__reviewTest = {
      state: opportunityReviewState,
      load: loadOpportunityReviews,
      history: loadOpportunityReviewHistory,
      decide: applyOpportunityReviewDecision
    };`, context);
  return {...context.__reviewTest, nodes, historyNode, getConfirms: () => confirms};
}

test("R10.0C3 review panel wired, C2 browser and old panel retained", () => {
  assert.match(js, /JARVIS_R100C3_REVIEW_QUEUE/);
  assert.match(css, /JARVIS_R100C3_REVIEW_QUEUE/);
  assert.match(js, /JARVIS_R100C2_COMMAND_CENTER/);
  assert.match(js, /JARVIS_R922D2_OPPORTUNITY_PANEL/);
  for (const control of ["#jba-or-filter", "#jba-or-refresh", "#jba-or-prev", "#jba-or-next"]) {
    assert.ok(js.includes(control));
  }
  assert.match(js, /void loadOpportunityReviews\(\)/);
});

test("Queue pages, validates contract, and escapes program names", async () => {
  const urls = [];
  const t = harness(async url => { urls.push(url); return fixture(12, {offset: Number(new URL(url, 'http://x').searchParams.get('offset')), records: fixture(12).records}); });
  await t.load();
  assert.match(urls[0], /state=pending/);
  assert.match(t.nodes["#jba-or-status"].textContent, /12 pending/);
  assert.match(t.nodes["#jba-or-page"].textContent, /Page 1 of 2/);
  assert.equal(t.nodes["#jba-or-next"].disabled, false);
  assert.equal(t.nodes["#jba-or-prev"].disabled, true);
  assert.match(t.nodes["#jba-or-records"].innerHTML, /GCash &lt;img/);
  assert.doesNotMatch(t.nodes["#jba-or-records"].innerHTML, /<img/);
  t.state.offset = 10;
  await t.load();
  assert.match(t.nodes["#jba-or-page"].textContent, /Page 2 of 2/);
  assert.equal(t.nodes["#jba-or-prev"].disabled, false);
});

test("Review-state filter encodes correctly", async () => {
  const urls = [];
  const t = harness(async url => {
    urls.push(url);
    return fixture(1, {counts:{pending:0,acknowledged:0,deferred:1,resolved:0},
      records:[{...fixture(1).records[0], review_state:"deferred"}]});
  });
  t.state.filter = "deferred";
  await t.load();
  assert.equal(new URL(urls[0], "http://x").searchParams.get("state"), "deferred");
  assert.match(t.nodes["#jba-or-records"].innerHTML, /deferred/);
});

test("Unsafe review response fails closed and disables navigation", async () => {
  const t = harness(async () => fixture(2, {execution_authorized:true}));
  await t.load();
  assert.equal(t.nodes["#jba-or-status"].textContent, "Unavailable");
  assert.match(t.nodes["#jba-or-records"].textContent, /Unsafe review queue response/);
  assert.equal(t.nodes["#jba-or-next"].disabled, true);
  assert.equal(t.state.records.size, 0);
});

test("Audit history displays entries with escaped actor and note", async () => {
  const t = harness(async url => {
    if (url.includes('/history')) return {
      ...fixture(1), status:"ready", event_id:1, review_state:"pending",
      total_history:1,
      records:[{id:1,request_id:"review-0000001",from_state:"deferred",to_state:"pending",
        actor:"<img onerror=bad()>", note:"<script>bad()</script>", changed_at:1795516940}]
    };
    return fixture(1);
  });
  await t.load();
  await t.history(1);
  assert.match(t.historyNode.innerHTML, /&lt;script&gt;/);
  assert.match(t.historyNode.innerHTML, /&lt;img/);
  assert.doesNotMatch(t.historyNode.innerHTML, /<script>|<img/);
});

test("Review decision requires confirmation and explicit intent header", async () => {
  const calls = [];
  const no = harness(async url => fixture(1), {confirmed:false});
  await no.load();
  assert.equal(await no.decide(1, "acknowledged", "reviewed"), false);
  assert.equal(no.getConfirms(), 1);

  let updated = false;
  const yes = harness(async (url, options = {}) => {
    if (options.method === "POST") {
      calls.push({url, options});
      updated = true;
      return {
        ...fixture(0), status:"updated", event_id:1, review_state:"acknowledged",
        request_id:JSON.parse(options.body).request_id,
      };
    }
    return updated ? fixture(0) : fixture(1);
  });
  await yes.load();
  assert.equal(await yes.decide(1, "acknowledged", "reviewed"), true);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].options.method, "POST");
  assert.equal(calls[0].options.headers["X-Jarvis-Review-Intent"], "review-state-only");
  assert.equal(JSON.parse(calls[0].options.body).expected_state, "pending");
  assert.equal(JSON.parse(calls[0].options.body).new_state, "acknowledged");
  assert.equal(yes.state.records.size, 0);
});

test("Failed requests retain idempotency key for explicit retry", async () => {
  const ids = [];
  let attempts = 0;
  const t = harness(async (url, options = {}) => {
    if (options.method === "POST") {
      ids.push(JSON.parse(options.body).request_id);
      attempts++;
      if (attempts === 1) throw new Error("Connection lost");
      return {...fixture(0), status:"already_applied", event_id:1,
        review_state:"deferred", request_id:ids[0]};
    }
    return attempts >= 2 ? fixture(0) : fixture(1);
  });
  await t.load();
  assert.equal(await t.decide(1, "deferred", "check scope"), false);
  assert.equal(await t.decide(1, "deferred", "check scope"), true);
  assert.equal(attempts, 2);
  assert.equal(ids[0], ids[1]);
});

test("Older responses do not overwrite newer review page", async () => {
  const waiting = [];
  const t = harness(url => new Promise(resolve => waiting.push({url,resolve})));
  const first = t.load();
  t.state.offset = 10;
  const second = t.load();
  waiting[1].resolve(fixture(12, {offset:10,records:fixture(12).records.slice(0,2)}));
  await second;
  assert.match(t.nodes["#jba-or-page"].textContent, /Page 2 of 2/);
  waiting[0].resolve(fixture(12));
  await first;
  assert.match(t.nodes["#jba-or-page"].textContent, /Page 2 of 2/);
});
