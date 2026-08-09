# Genesis IX-A4.7 Pack 1 — Executive Conversation Grounded Answer Runtime Interface

## Mission

Define the canonical adapter between the Executive conversation runtime and the
IX-A4.6 Grounded Answer Engine without changing live runtime behavior.

## Interface

```text
Executive conversation context
        +
QualificationResult
        ↓
GroundedAnswerExecutionRequest
        ↓
GroundedAnswerRuntimeService
        ↓
GroundedAnswerPlan
        ↓
GroundedAnswerExecutionResponse
```

## Operations

### `plan(request)`

Builds a `GroundedAnswerPlan` and does not invoke synthesis.

### `execute(request, synthesis_handler)`

Builds the plan and invokes an explicitly supplied synthesis handler.

No current conversation or orchestrator component calls either operation in
Pack 1.

## Guarantees

- stable immutable request context;
- canonical request and response serialization;
- explicit synthesis invocation state;
- citations, conflicts, confidence, and knowledge state projected from the
  plan;
- no changes to `ExecutiveConversationService`;
- no changes to `ExecutiveConversationOrchestrator`;
- no changes to `ExecutiveDirector`;
- no changes to API routes or Mission Control.
