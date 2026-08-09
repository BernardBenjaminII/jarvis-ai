
# Genesis VII-A0 Pack 4B-2 — Executive Capability Orchestration Layer

**Status:** Implemented
**Authority:** Genesis VII-A0
**Scope:** Deterministic capability discovery, selection, dependency planning, health projection, and explainability.

## Decision

The Executive Director does not select or invoke concrete tools directly. It submits a
`CapabilityRequirement` to the `CapabilityOrchestrator`. The orchestrator validates the
capability graph, scores eligible candidates deterministically, selects one capability,
constructs a dependency-ordered plan, and returns an inspectable decision.

## Constitutional Boundaries

1. The pack is additive and does not replace the existing capability loader or registry.
2. The orchestration core performs no network access, model invocation, shell execution,
   filesystem mutation, or vendor-specific integration.
3. Identical registry state and identical requirements produce identical selection and
   plan fingerprints.
4. Failed and disabled capabilities cannot be selected.
5. Permissions, cost, latency, risk, inputs, and outputs are explicit selection constraints.
6. Dependency cycles and missing dependencies prevent planning.
7. Mission Control consumes only the read-only observability snapshot.

## Public API

- `CapabilityMetadata`
- `CapabilityRequirement`
- `CapabilityRegistry`
- `CapabilityGraph`
- `CapabilitySelector`
- `CapabilityPlanner`
- `CapabilityOrchestrator`
- `CapabilityObservabilityService`
- `OrchestrationDecision`

## Follow-on Integration

A later pack may adapt the existing runtime capability registry into this metadata model,
publish the observability snapshot through Executive Operations routes, and execute approved
plans. Pack 4B-2 intentionally stops before execution.
