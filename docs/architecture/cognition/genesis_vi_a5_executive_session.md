# Genesis VI-A5 — Executive Session

**Status:** Implemented  
**Package:** `core.cognition`  
**Primary module:** `core/cognition/session.py`

## Constitutional Law

> Cognition cycles exist only within a stable executive session that preserves
> mission identity, executive identity, authority, and lifecycle continuity.

## Purpose

VI-A5 introduces the mission-scoped owner above individual cognition cycles.
A session can create and retain multiple cycles while enforcing that only one
cycle may actively consume executive attention at a time.

## Capabilities

- stable `session_id`, `mission_id`, and `executive_id`;
- session-level authority inheritance;
- deterministic cycle admission and lookup;
- single-active-cycle enforcement;
- session-routed cycle transitions, memory, and notes;
- completed, failed, and suspended cycle retention;
- immutable session snapshots;
- monotonic session audit events;
- controlled session closure.

## Boundary

VI-A5 is deliberately process-local. It does not serialize sessions or restore
them after process termination. Genesis VI-A6 will add persistence, checkpoints,
replay, schema versions, and recovery without changing session semantics.
