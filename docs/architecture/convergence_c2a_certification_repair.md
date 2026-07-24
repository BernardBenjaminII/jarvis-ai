# JARVIS Convergence C-2A — Certification Repair

## Status

Certification repair for Convergence C-2 Director Activation.

## Purpose

C-2 replaced the C-1 legacy answer-handler path with the canonical
`ExecutiveConversationOrchestrator`. The original C-1 HTTP test continued to
patch `conversation_service.answer_handler`, which is no longer the active
production execution boundary. Consequently, the test invoked the live Ollama
model and compared that real response with the obsolete deterministic value
`ok:status`.

C-2A repairs the certification harness without changing production behavior.

## Contract

The HTTP contract now patches only
`conversation_orchestrator.synthesis_handler` during tests. This preserves real
HTTP routing, request compilation, mission creation, Director activation,
mission persistence, response serialization, and conversation persistence while
removing live-model variability from deterministic certification.

Production continues to configure:

```python
synthesis_handler=route_question
```

No production service, route, Director, mission, or orchestration implementation
is replaced by this pack.

## Test Separation

- **Deterministic certification:** C-1, C-2, and C-2A unit and HTTP contracts.
- **Operational model validation:** performed separately when a live Ollama
  response is intentionally required.

This separation prevents model latency or nondeterministic wording from
invalidating architecture certification.
