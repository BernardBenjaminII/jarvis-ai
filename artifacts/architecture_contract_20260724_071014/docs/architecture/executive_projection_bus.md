# Genesis VI-A3 — Executive Projection Bus

The Executive Projection Bus is the canonical read-only integration boundary
between JARVIS subsystems and the Commander's Bridge.

The Bridge consumes projections, never subsystem internals.

## Readiness contract

- `green` / `good`: ready.
- `yellow` / `caution`: usable with warnings or partial degradation.
- `red` / `bad`: unavailable or not reliable.

## Endpoints

- `GET /operations/bridge`
- `GET /operations/bridge/readiness`
- `GET /operations/bridge/manifest`
- `GET /operations/bridge/projections/{projection_id}`

Legacy `/operations/projections` endpoints remain available.

## Invariants

1. Read-only integration.
2. Canonical singleton runtime.
3. Deterministic projection ordering.
4. Semantic fingerprinting.
5. Revisions change only when semantic state changes.
6. UI colors derive from health, never manual configuration.
7. Diagnostic details remain available through projection drill-down.
8. New subsystems become visible by registering a projection provider.

VI-A3 supplies the permanent backend contract for future Knowledge, Reasoning,
Cognition, Operations, Voice, Vision, and Executive Intelligence UI panels.
