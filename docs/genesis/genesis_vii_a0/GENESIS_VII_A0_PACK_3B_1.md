# Genesis VII-A0 — Pack 3B-1

## Executive API Client

**Status:** Implemented  
**Depends on:** Pack 2 and Pack 3A-3.1

## Purpose

Pack 3B-1 establishes the canonical browser-side client for the Executive
Operations Center REST API.

## API Methods

- `JARVIS_API.dashboard()`
- `JARVIS_API.health()`
- `JARVIS_API.metrics()`
- `JARVIS_API.status()`
- `JARVIS_API.eventsEndpoint()`
- `JARVIS_API.liveStatus()`
- `JARVIS_API.request()`

## Contract

The client expects Pack 2 transport envelopes containing:

- `ok`
- `resource`
- `data`
- `transport_version`

The client rejects malformed or mismatched transport responses.

## Reliability

The client provides:

- request identifiers;
- request timeouts;
- bounded GET retries;
- exponential backoff with jitter;
- structured API errors;
- browser and JARVIS runtime events;
- same-origin credentials;
- no-store cache behavior.

## Constitutional Rules

1. The client shall not invent missing data.
2. Non-successful HTTP responses shall remain visible.
3. Invalid transport envelopes shall be rejected.
4. Retry behavior shall remain bounded.
5. POST or other mutating requests shall not be retried automatically.
6. All future dashboard bindings shall use this client rather than direct
   ad hoc `fetch()` calls.

## Browser Inspection

```javascript
JARVIS_API.version
JARVIS_API.diagnostics()
await JARVIS_API.dashboard()
