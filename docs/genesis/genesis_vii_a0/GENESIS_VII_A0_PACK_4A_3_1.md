# Genesis VII-A0 — Pack 4A-3.1

## Executive Publisher Wiring

**Status:** Implemented

## Defect Corrected

Pack 2 retained a placeholder route at:

```text
GET /operations/executive/events
```

Pack 4A-3 introduced the canonical event-runtime route at the same path.
FastAPI resolves duplicate paths in registration order. The compatibility
router was registered first, so the placeholder response masked the canonical
Timeline repository.

## Constitutional Resolution

The canonical Event Runtime router now precedes the Pack 2 compatibility
router.

```text
executive_event_runtime_router
        ↓
executive_operations_router
```

The authoritative endpoint now returns:

- `configured = true`;
- `integration_state = configured`;
- persisted constitutional events;
- total and returned event counts;
- repository integrity state;
- terminal fingerprint.

## Startup Evidence

Entering the FastAPI lifespan publishes:

- `executive_boot_started`;
- `executive_boot_completed`.

These events are immediately visible through the authoritative endpoint and
the Mission Control timeline projection.

## Scope

This pack corrects route ownership and repository visibility. It does not add
WebSocket dependencies; Pack 4B-1 continues to use REST polling when live
transport is unavailable.

## Next Pack

Genesis VII-A0 Pack 4B-1-R1 — Live transport enablement, or Pack 4B-2 —
timeline filtering and mission correlation.
