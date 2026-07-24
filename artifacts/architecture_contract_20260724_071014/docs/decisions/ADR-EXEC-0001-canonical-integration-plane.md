# ADR-EXEC-0001: Canonical Executive Integration Plane

**Status:** Proposed  
**Date:** 2026-07-23

## Context

JARVIS contains multiple mature backend systems, but API and UI integration is inconsistent. Directly wiring each frontend component to internal packages would produce duplicated contracts, hidden coupling, and repeated drift.

## Decision

Create a canonical Executive Integration Plane between domain systems and all external interfaces.

The plane will provide:

- capability discovery
- normalized state projections
- command routing
- health/degradation reporting
- provenance
- audit correlation
- stable transport contracts

The existing capability registry will become the canonical source for capability visibility.

## Consequences

### Positive

- UI can render capabilities dynamically.
- Backend changes no longer require arbitrary frontend rewrites.
- Missing integration becomes measurable.
- Failure and unavailable states become visible.
- Every command can be correlated with evidence and timeline events.

### Negative

- Requires adapters around existing subsystems.
- Introduces schema governance.
- Forces removal of placeholder telemetry.
- Exposes inconsistencies previously hidden between packages.

## Rejected alternatives

1. Direct frontend imports or database access.
2. Separate ad hoc endpoint styles for every subsystem.
3. Hard-coded UI capability menus.
4. Treating API availability as proof of operational readiness.
