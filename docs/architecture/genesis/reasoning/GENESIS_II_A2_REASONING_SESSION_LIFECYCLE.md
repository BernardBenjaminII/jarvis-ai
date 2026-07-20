# Genesis II-A2 — Reasoning Session Lifecycle

**Document ID:** `GENESIS-II-A2`  
**Version:** `1.0.0`  
**Status:** Implementation Candidate  
**Subsystem:** Reasoning  
**Depends On:** Genesis II-A1 Reasoning Session Contract  
**Authority:** Executive Architecture Council

## Purpose

Genesis II-A2 defines the deterministic lifecycle governing immutable
`ReasoningSession` snapshots. II-A1 established what a reasoning session is;
II-A2 establishes how it may constitutionally evolve.

## Constitutional Boundary

The lifecycle may validate transitions, create successor snapshots, increment
revisions by exactly one, preserve protected fields, and expose deterministic
transition policy.

It may not mutate sessions, execute `ReasoningEngine`, retrieve evidence,
generate identifiers or timestamps, access networks or persistence, launch
processes, authorize missions, create plans, or exercise Executive authority.

## Lifecycle Model

```text
CREATED
    |
    v
INITIALIZED
    |
    v
COLLECTING_EVIDENCE
    |
    v
REASONING
    |
    v
REVIEW
    |
    v
COMPLETED
```

Every active state may transition to `FAILED` or `CANCELLED`. `REVIEW` may
return to `COLLECTING_EVIDENCE` or `REASONING`.

## Terminal States

`COMPLETED`, `FAILED`, and `CANCELLED` have no legal successors. Restarting
work requires a new session identity and an explicit relationship to the
terminal session.

## Revision and Immutability Law

Every accepted transition creates a new immutable snapshot and increments
`revision` by exactly one. All fields other than `state` and `revision` remain
equal. The predecessor is never rewritten.

## Determinism Law

Equivalent session snapshots and target states must produce equivalent
successor snapshots. Lifecycle behavior may not depend on time, randomness,
environment state, network state, persistence state, or memory address.

## Public API

```python
ReasoningSessionLifecycle.transition(session, target_state)
ReasoningSessionLifecycle.can_transition(source_state, target_state)
ReasoningSessionLifecycle.allowed_targets(source_state)
ReasoningSessionLifecycle.is_terminal(state)
```

`LifecycleManager` is a stable alias for `ReasoningSessionLifecycle`.

## Certification Requirements

II-A2 passes only when:

- the package compiles;
- stable public imports succeed;
- II-A1 regression tests pass;
- II-A2 lifecycle tests pass;
- every state is governed;
- the transition map is immutable;
- terminal states have no successors;
- transitions create new snapshots;
- revisions advance by exactly one;
- protected fields remain unchanged;
- illegal transitions fail;
- forbidden runtime imports are absent; and
- the certified `ReasoningEngine` remains importable.

## Explicitly Deferred

This phase does not introduce persistence, lifecycle event records, transition
reasons, actors, evidence provenance, budgets, Executive governance,
orchestration, engine invocation, recovery, or distributed coordination.

## Constitutional Declaration

A reasoning session may evolve only through an explicit, deterministic,
validated transition. No snapshot may be rewritten, and no terminal session
may be reopened.

**Architecture is earned. Certification is evidence. Evolution is governed.**
