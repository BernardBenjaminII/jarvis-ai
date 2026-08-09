# Genesis IX-A4.5 Pack 2A — Evidence Qualification Engine

Implements deterministic lexical, phrase, subject, confidence, entity, and provenance qualification against the Pack 1A contracts.

Canonical API:

```python
QualificationEngine.evaluate(query, candidates) -> QualificationResult
```

This pack does not modify retrieval, grounding, awareness, Director, or conversation behavior.
