# ADR-EXEC-0002 — Canonical Executive Projection Bus

**Status:** Accepted  
**Phase:** Genesis VI-A3

## Decision

JARVIS shall expose all UI-visible subsystem state through one canonical
Executive Projection Bus. Mission Control shall not call subsystem internals.

Every visible subsystem supplies a projection provider. The Bus aggregates the
registered projections, derives red/yellow/green readiness, and exposes a
stable Bridge API.

## Consequences

- The UI has one integration surface.
- New subsystems become visible through registration rather than hard-coded UI
  coupling.
- Readiness remains simple on the Bridge.
- Full diagnostics remain available on drill-down.
- Projection contracts become compatibility boundaries.

Direct UI-to-subsystem calls and static dashboard configuration are rejected.
