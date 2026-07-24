# Genesis VI-A6.6 — Executive Lifecycle & Session Manager

**Status:** Implemented  
**Layer:** Executive Continuity  
**Depends on:** Genesis VI-A6.1 through VI-A6.5

## Purpose

Genesis VI-A6.6 introduces the conductor for the Executive continuity stack.

It owns:

- Executive boot,
- readiness,
- session creation,
- mission activation,
- checkpoint coordination,
- suspension,
- certified recovery invocation,
- mission resumption,
- completion,
- abort,
- orderly shutdown.

## Lifecycle

```text
OFFLINE
   ↓
BOOTING
   ↓
READY
   ↓
ACTIVE
   ├── CHECKPOINTING ──→ ACTIVE
   ├── SUSPENDED ──→ RECOVERING ──→ ACTIVE
   ├── READY
   └── SHUTTING_DOWN ──→ OFFLINE
```

Failures transition the manager to `FAILED`.

## Architectural Boundary

The lifecycle manager coordinates but does not duplicate lower-level work.

It does not:

- serialize Executive state,
- write checkpoint files directly,
- validate cryptographic integrity,
- select recovery points internally,
- reconstruct state itself.

Those responsibilities remain in Genesis VI-A6.2 through VI-A6.5.

## Event Evidence

Every lifecycle action produces an immutable event containing:

- monotonic sequence,
- event kind,
- lifecycle state,
- session identifier,
- detail,
- timestamp,
- event fingerprint.

These events are the future source for:

- Mission Control status panels,
- the Executive timeline,
- recovery prompts,
- audit views,
- deterministic replay.

## UI Relationship

Mission Control should consume lifecycle state rather than inventing it.

Examples:

```text
READY        → Executive Online
ACTIVE       → Mission Active
CHECKPOINTING→ Saving Executive State
SUSPENDED    → Mission Interrupted
RECOVERING   → Restoring Certified Session
FAILED       → Executive Intervention Required
OFFLINE      → Executive Offline
```

This phase establishes the authoritative backend state machine that the UI will
visualize.
