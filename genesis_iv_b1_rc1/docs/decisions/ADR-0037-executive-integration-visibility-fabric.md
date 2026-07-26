# ADR-0037 — Executive Integration and Visibility Fabric

**Status:** Accepted  
**Milestone:** Genesis IV-B1

## Decision

Create `core.integration` as the canonical projection and coordination boundary
for capability registration, repository wiring audit, knowledge readiness,
Executive API contracts, and Mission Control projections.

The fabric shall not own observation, cognition, evidence, mission persistence,
execution, or UI state. It shall expose those domains without duplicating them.
