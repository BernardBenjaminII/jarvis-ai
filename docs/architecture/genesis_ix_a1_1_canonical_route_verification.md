
# Genesis IX-A1.1 — Canonical Route Verification

**Campaign:** Genesis IX / Mark I
**Predecessor:** Genesis IX-A1

## Objective

Remove Genesis verification's dependency on FastAPI private routing internals.
The installed FastAPI version stores `app.include_router()` registration records
as private `_IncludedRouter` objects without public route paths or methods.

## Canonical Boundary

IX-A1.1 verifies JARVIS-owned `APIRouter` objects directly and converts their
public route collections into immutable `RouteContract` values. It does not
inspect `_IncludedRouter`, `_RouterIncludeContext`, or other private framework
implementation details.

## Certified Conversation Contracts

```text
POST /ask
POST /api/conversation/query
GET  /api/conversation/sessions/{session_id}
GET  /api/conversation/sessions/{session_id}/messages
```

IX-A1.1 changes verification only. It does not modify application routing,
endpoint implementation, or Mission Control runtime behavior.
