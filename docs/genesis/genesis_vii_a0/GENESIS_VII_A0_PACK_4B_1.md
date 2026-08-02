# Genesis VII-A0 — Pack 4B-1

## Mission Control Executive Event Timeline Projection

**Status:** Implemented

Loads certified history from `GET /operations/executive/events?limit=100`,
consumes live `executive.event` WebSocket envelopes, orders by descending
sequence, deduplicates by `event_id`, reconnects with bounded backoff, and
falls back to REST polling when live transport is unavailable.

Each event exposes timestamp, kind, subsystem, summary, context, sequence,
identifier, fingerprint, and payload. DOM construction avoids `innerHTML`.

## Next Pack

Genesis VII-A0 Pack 4B-2 — Event filtering, correlation, and mission drill-down.
