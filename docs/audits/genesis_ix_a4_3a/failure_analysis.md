# Genesis IX-A4.3A — Certification Failure Analyzer

**Status:** **ANALYZED**
**Source status:** **FAILED**
**Failed checks:** **2**

## Summary

- Blocking failures: **2**
- Non-blocking failures: **0**
- Next action: Repair blocking runtime failures before changing certification thresholds.

## `GAP-DECLARATION` — Knowledge gap is explicit

- Classification: `RUNTIME_BUG`
- Confidence: 0.93
- Blocking: True
- Repair scope: runtime gap handling
- Reason: Unknown material did not produce an explicit KnowledgeGap.
- Recommended repair: Repair CatalogGroundingService gap creation and prompt propagation.

### Evidence

- Status: 'grounded'
- Gap count: 0
- Unknown material must generate an explicit KnowledgeGap.

## `GAP-RECOMMENDATION` — Gap prompt preserves acquisition guidance

- Classification: `RUNTIME_BUG`
- Confidence: 0.93
- Blocking: True
- Repair scope: runtime gap handling
- Reason: Unknown material did not produce an explicit KnowledgeGap.
- Recommended repair: Repair CatalogGroundingService gap creation and prompt propagation.

### Evidence

- Status: 'grounded'
- Gap count: 0
- The gap must retain a recommended follow-on action.
