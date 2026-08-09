# Genesis IX-A2 — Conversation Integration

IX-A2 connects the Mission Control Knowledge Workspace to the existing
Executive Conversation Runtime through a normalized adapter.

## Canonical endpoint

```text
POST /api/knowledge/conversation
```

The route delegates to the existing `conversation_service.ask` implementation.
It does not create a parallel conversation engine.

## Response contract

The workspace receives normalized status, answer, session identity,
confidence, latency, sources, evidence, activity, and safe error information.

## Compatibility

The existing `/api/conversation/query` and `/ask` endpoints remain available
as client fallbacks.
