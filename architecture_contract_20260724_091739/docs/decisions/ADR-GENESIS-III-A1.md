# ADR — Explicit Immutable Cognitive Workspace

**Status:** Accepted  
**Milestone:** Genesis III-A1  
**Decision scope:** Cognitive architecture

## Context

JARVIS already possesses reasoning contracts, reasoning services, knowledge
integration, sessions, constitutional context, and canonical evidence.

However, active reasoning still requires a durable conceptual container.
Without one, hypotheses, assumptions, evidence under consideration, unresolved
questions, and confidence changes risk remaining implicit or transient.

## Decision

Introduce an explicit immutable cognitive workspace.

The workspace shall:

1. represent one active reasoning objective;
2. maintain hypotheses, evidence references, assumptions, and questions;
3. record every valid transition as an append-only event;
4. return a new revision for every mutation;
5. prohibit mutation of terminal workspaces;
6. expose deterministic snapshots for orchestration and presentation;
7. remain persistence-agnostic at this stage.

## Consequences

### Positive

- Reasoning state becomes inspectable and auditable.
- Hidden mutable cognitive state is reduced.
- Later persistence and concurrency controls have a stable domain model.
- UI and executive layers can consume a concise workspace snapshot.
- Reasoning-engine outputs can be attached without redefining the model.

### Negative

- More objects and transitions must be managed explicitly.
- Persistence and distributed coordination remain future work.
- Event history grows monotonically.

## Rejected alternatives

### Store reasoning state in unstructured dictionaries

Rejected because dictionaries provide weak invariants and unstable interfaces.

### Make workspace objects mutable

Rejected because in-place mutation weakens auditability and revision tracking.

### Couple the workspace directly to a database

Rejected because persistence policy should remain separate from domain contracts.
