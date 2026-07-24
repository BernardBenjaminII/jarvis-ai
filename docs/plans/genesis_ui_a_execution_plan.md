# Genesis UI-A Execution Plan

## UI-A1 — Executive Integration Audit

### Goal

Determine exactly what exists, what is exposed, what is live, and what remains disconnected.

### Deliverables

- subsystem inventory
- API route inventory
- UI surface inventory
- capability registry inventory
- placeholder telemetry findings
- integration matrix
- prioritized gaps

### Exit criteria

Every major subsystem has one of these classifications:

- fully integrated
- API-only
- backend-only
- UI placeholder
- unavailable
- deprecated
- unknown

## UI-A2 — Canonical REST Layer

### Goal

Provide stable read contracts for all executive subsystems.

### Required routes

- executive
- capabilities
- knowledge
- reasoning
- missions
- acquisition
- runtime
- timeline
- health

### Exit criteria

- OpenAPI includes every route.
- Every route has schema tests.
- Every projection reports health.
- No endpoint returns invented values.

## UI-A3 — Live Telemetry Replacement

### Goal

Remove mock and placeholder state.

### Work

- trace every displayed metric to a provider;
- record provider and timestamp;
- show unknown/degraded states;
- add caching only where required;
- add integration tests against controlled fixtures.

### Exit criteria

Every UI metric has a documented source.

## UI-A4 — Dynamic Capability Explorer

### Goal

Build the UI from capability descriptors.

### Work

- expose capability registry;
- normalize descriptor schema;
- render capability groups;
- show availability and degradation;
- generate action forms from operation schemas;
- record results in timeline.

### Exit criteria

A newly registered capability appears without hard-coded navigation changes.

## UI-A5 — Executive Workspace Binding

### Goal

Connect Commander Brief, Mission Workspace, SITREP, Journal, alerts, objectives, tasks, activities, and recommendations to real executive state.

### Exit criteria

- active mission is live;
- mission hierarchy is navigable;
- actions use real command paths;
- decisions and activities appear in timeline;
- failures are visible.

## UI-A6 — Knowledge and Reasoning Transparency

### Goal

Expose JARVIS knowledge awareness and reasoning state.

### Exit criteria

The user can see:

- what JARVIS knows;
- why it believes it;
- confidence and contradiction;
- what is missing;
- recommended sources;
- acquisition and ingestion progress;
- whether the gap was resolved.

## Recommended branch

```bash
git checkout -b feature/genesis-ui-a-executive-integration
```

## Recommended commit sequence

```text
1. Add executive integration contracts and audit
2. Add canonical subsystem projections
3. Replace placeholder telemetry with live providers
4. Expose canonical capability registry API
5. Bind Commander Brief and Mission Workspace
6. Add knowledge coverage and research queue surfaces
7. Add reasoning transparency and provenance
8. Certify Genesis UI-A
```
