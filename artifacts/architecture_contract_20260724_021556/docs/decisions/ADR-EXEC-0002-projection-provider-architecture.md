# ADR-EXEC-0002: Projection Provider Architecture

**Status:** Accepted  
**Date:** 2026-07-23

## Decision

All UI-facing subsystem state passes through registered `ProjectionProvider` adapters and versioned `ProjectionEnvelope` contracts. The `ExecutiveProjectionService` is the canonical read facade.

## Consequences

- Subsystem integration becomes additive.
- UI contracts remain stable.
- Missing and degraded state are explicit.
- Existing domain services remain authoritative.
- Provider tests define the integration boundary.
