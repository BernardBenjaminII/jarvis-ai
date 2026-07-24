# Genesis VI-A3 — Cognitive State Machine

**Status:** Implemented  
**Package:** `core.cognition`  
**Primary module:** `core/cognition/state_machine.py`

## Purpose

Genesis VI-A3 establishes the authoritative deterministic controller for
executive cognitive state. Every future component that changes executive state
must request a validated transition through this controller.

## Core Principle

> Everything that changes executive state must pass through the Cognitive
> State Machine.

This prevents hidden state mutation and makes executive behavior auditable,
replayable, and testable.

## Capabilities

- immutable transition policy;
- explicit legal-transition graph;
- deterministic transition validation;
- self-transition rejection;
- optional transition guards;
- immutable transition history;
- lifecycle event emission;
- immutable audit snapshots;
- deterministic path execution;
- validated replay from transition history;
- controlled suspension and recovery paths;
- terminal completion enforcement.

## Canonical Lifecycle

```text
IDLE
  -> INITIALIZING
  -> OBSERVING
  -> ATTENDING
  -> RETRIEVING (optional)
  -> REASONING
  -> EVALUATING
  -> PLANNING
  -> AWAITING_AUTHORITY (optional)
  -> EXECUTING
  -> REFLECTING
  -> COMPLETED
```

Failure and suspension are explicit lifecycle states rather than exceptions
hidden outside the executive history.

## Architectural Boundaries

The state machine:

- does not perform observation;
- does not retrieve knowledge;
- does not reason;
- does not plan;
- does not execute actions;
- does not persist itself;
- does not call external models or networks.

It governs when specialist components are permitted to act.

## Public API

- `CognitiveStateMachine`
- `TransitionPolicy`
- `TransitionGuard`
- `StateMachineSnapshot`
- `DEFAULT_TRANSITION_POLICY`

## Next Phase

Genesis VI-A4 should introduce the cognition-cycle controller that combines
executive context, working memory, and the cognitive state machine into one
authoritative lifecycle aggregate.
