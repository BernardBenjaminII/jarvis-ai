# ADR-0022: Establish the Observation Engine

**Status:** Accepted  
**Decision date:** 2026-07-21  
**Release:** Genesis IV-R2

## Context

JARVIS requires a governed method for converting acquired information into
auditable cognitive records. Existing observation structures are insufficient
as the permanent foundation for evidence, claims, hypotheses, and reasoning.

## Decision

Create a dedicated Observation Engine under:

```text
core/cognition/layers/observation/
```

The engine uses immutable records, explicit provenance, deterministic
normalization, lifecycle governance, registry-backed retrieval, conservative
duplicate and conflict detection, merge operations, and typed relationships.

The release remains additive and does not redirect existing public cognition
imports.

## Consequences

### Positive

- independently certified cognition layer
- stable foundation for the Evidence Engine
- deterministic object identity and serialization
- explicit lifecycle and provenance
- safe migration path from legacy observation models

### Negative

- temporary coexistence with legacy observation structures
- in-memory registry is not durable
- deterministic conflict detection is intentionally conservative

## Follow-on decisions

- durable observation registry
- legacy facade adapter
- evidence-association contracts
- semantic contradiction analysis through the Reasoning Engine
