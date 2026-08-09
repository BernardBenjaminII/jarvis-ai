# Genesis IX-A4.7 Pack 2 — Executive Orchestrator Integration

This pack integrates the IX-A4.6 Grounded Answer Engine into the live Executive
Conversation Orchestrator.

```text
QualificationResult
    ↓
CatalogGroundingService
    ↓
ExecutiveKnowledgeAwarenessService
    ↓
GroundedAnswerRuntimeService.plan()
    ↓
GroundedAnswerPlan
    ↓
existing synthesis handler
```

The current request's `QualificationResult` is retained in a `ContextVar`.
The orchestrator appends the grounded-answer contract after the existing
grounding and awareness prompt sections.

Public conversation APIs remain unchanged, and synthesis is still invoked
exactly once.
