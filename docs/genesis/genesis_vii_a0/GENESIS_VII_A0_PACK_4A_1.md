# Genesis VII-A0 — Pack 4A-1

## Constitutional Executive Event Bus Integration

**Status:** Implemented

## Decision

JARVIS uses a closed constitutional event registry.

`TimelineSubsystem` and `TimelineEventKind` remain authoritative enums.
Runtime registration of arbitrary subsystem or event-kind strings is forbidden.

## Canonical Event Flow

```text
TimelineEventDraft
        ↓
ExecutiveEventBus
        ↓
ExecutiveTimelineEngine
        ↓
TimelineEvent
        ↓
ExecutiveTimelineRepository
        ↓
Subscribers
        ↓
Existing Executive live transport adapters
```

## Existing Authorities Reused

- `TimelineEventDraft` — publication request
- `TimelineEvent` — immutable Executive event
- `ExecutiveTimelineEngine` — event creation and fingerprint chain
- `ExecutiveTimelineRepository` — persistent append-only authority
- `ExecutiveLiveBroker` — existing WebSocket fan-out transport

## New Capability

`ExecutiveEventBus` establishes one constitutional publication boundary. It:

1. accepts only `TimelineEventDraft`;
2. enforces closed enum membership;
3. creates events through the Timeline Engine;
4. persists events before notifying subscribers;
5. isolates subscriber failures;
6. hydrates from existing repository history;
7. exposes repository integrity verification.

## Persistence Rule

An event is observable only after repository append succeeds.

Subscriber failure cannot roll back a committed event. If repository append
fails, the in-memory engine is rebuilt from the repository's certified state.

## Runtime Root

The lazy default runtime resolves:

1. `JARVIS_EXECUTIVE_TIMELINE_ROOT`, when configured;
2. otherwise `artifacts/runtime/executive_timeline`.

No persistent state is created during module import.

## Live Transport

`ExecutiveLiveEventBridge` converts committed `TimelineEvent` objects into
existing `ExecutiveLiveEnvelope` messages of type `executive.event`.

## Constitutional Amendment Rule

New directorates and event kinds require edits to the closed enums, tests,
documentation, and certification. Plugins may not invent event names at runtime.

## Next Pack

Genesis VII-A0 Pack 4A-2 — Executive Event Publishers and subsystem adapters.
