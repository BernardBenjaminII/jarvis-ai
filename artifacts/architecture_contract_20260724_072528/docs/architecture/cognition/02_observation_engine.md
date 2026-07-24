# Genesis IV-R2 Observation Engine

## Mission

The Observation Engine converts sourced inputs into immutable, validated,
auditable records suitable for evidence construction, claim formation,
hypothesis generation, reasoning, and executive action.

## Processing path

```text
Raw input
   ↓
ObservationInput
   ↓
Validation
   ↓
Normalization
   ↓
ObservationFactory
   ↓
ObservationRecord
   ↓
Lifecycle activation
   ↓
ObservationRegistry
   ↓
Query / comparison / merge / supersession / relationships
```

## Architectural boundaries

The engine depends on:

```text
core.cognition.common.object_model
```

It does not depend on:

- evidence
- claims
- hypotheses
- interpretation
- reasoning
- executive
- UI

Higher cognition layers may consume observations, but the Observation Engine
must remain independently certifiable.

## Deterministic versus semantic analysis

R2 implements conservative deterministic duplicate and conflict detection.

It intentionally does not claim full semantic contradiction detection.
Reasoning-assisted semantic analysis belongs in a later integration phase.

## Persistence

R2 provides a thread-safe in-memory registry contract. Durable persistence is
deferred until the registry interface has been exercised by later cognition
layers. This avoids prematurely binding the cognitive architecture to a
specific database implementation.

## Compatibility strategy

R2 does not replace the legacy public Observation facade. Adoption will occur
through a later adapter and redirection release after behavioral equivalence is
demonstrated.
