# JARVIS Convergence C-1 — Executive Conversation Activation

## Decision

JARVIS exposes one canonical conversation boundary to the operator. Text, and later voice, enter the same service. The service compiles the request into one or more provisional objectives, persists the exchange, invokes the active JARVIS answer path, and returns a stable structured response.

## Boundary

```text
Operator
  -> Bridge conversation UI
  -> POST /api/conversation/query
  -> ExecutiveConversationService
  -> ExecutiveRequestCompiler
  -> current core.src.brain.route_question adapter
  -> structured response + persisted history
```

C-1 does not claim to complete director activation, knowledge grounding, or multimodal voice. It creates the stable operator and API boundary through which those packs will operate.

## Invariants

1. The UI does not invoke model services directly.
2. The legacy `/ask` route remains compatible.
3. Conversation history is durable in SQLite.
4. Every response carries a request ID, session ID, state, objectives, and trace.
5. Compound requests may produce several provisional objectives while remaining one operator turn.
6. Future orchestrators replace the injected answer handler without changing the browser contract.
