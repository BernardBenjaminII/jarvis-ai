# Genesis IX-A4.6 — Grounded Answer Engine

Transforms `QualificationResult` into an inspectable grounded-answer plan.

```text
QualificationResult
    ↓
evidence ranking
    ↓
conflict detection
    ↓
citation generation
    ↓
confidence calibration
    ↓
GroundedAnswerPlan
    ↓
synthesis handler
    ↓
GroundedAnswer
```

Knowledge states: `known`, `partial`, `unknown`, and `conflicted`.

This foundation changes no live conversation-path behavior.
