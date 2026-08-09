# Genesis VII-A0 — Pack 4A-3

## Executive Runtime Bootstrap Integration

**Status:** Implemented

## Purpose

Install one process-wide constitutional Executive Event Runtime into the
FastAPI application lifecycle.

## Runtime Composition

```text
FastAPI lifespan
        ↓
ExecutiveEventRuntime
        ├── ExecutiveEventBus
        ├── ExecutiveTimelineRepository
        ├── ExecutiveLiveEventBridge
        └── Existing ExecutiveLiveBroker
```

## Startup

Application startup:

1. installs the Event Runtime into `app.state`;
2. subscribes the live-event bridge;
3. publishes `executive_boot_started`;
4. verifies the timeline repository;
5. publishes `executive_boot_completed`.

## Shutdown

Application shutdown publishes:

- `executive_shutdown_started`
- `executive_shutdown_completed`

The live bridge is then removed cleanly.

## Application State

The following authorities are exposed:

- `app.state.executive_event_runtime`
- `app.state.executive_event_bus`
- `app.state.executive_timeline_repository`

## API Projections

```text
GET /operations/executive/event-runtime
GET /operations/executive/events?limit=100
```

These routes expose runtime status and certified constitutional history.

## Existing Infrastructure Reused

- the Operations Center's `ExecutiveLiveBroker`;
- the persistent Executive Timeline repository;
- the constitutional Event Bus from Pack 4A-1;
- publisher migrations from Pack 4A-2.

## Import-Time Rule

Runtime construction may resolve repository state, but no lifecycle event is
published until FastAPI enters its lifespan. No background task is launched
during module import.

## Next Pack

Genesis VII-A0 Pack 4B-1 — Mission Control Executive Event Timeline Projection.
