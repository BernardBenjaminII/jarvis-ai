# Genesis IX-A5 Pack 3 — Qualification Recall Forensics

## Mission

Explain every qualification acceptance and rejection without changing runtime
qualification behavior.

## Forensic Flow

```text
Canonical probe
    ↓
Raw search
    ↓
Qualified search
    ↓
Qualification diagnostics
    ↓
Candidate score decomposition
    ↓
Rejection reason classification
    ↓
Recall analysis
    ↓
Deterministic recommendations
```

## Candidate Record

Each candidate records:

- raw rank;
- retrieval score;
- lexical score;
- phrase score;
- subject score;
- confidence score;
- final score;
- threshold;
- score margin;
- decision;
- rejection reason;
- explanation;
- source path.

## Rejection Classes

- `LEXICAL`
- `PHRASE`
- `SUBJECT`
- `CONFIDENCE`
- `FINAL_THRESHOLD`
- `UNKNOWN`

## Safety

Pack 3 is read-only. It does not modify qualification thresholds, weights,
normalization, retrieval, catalog data, FTS tables, or runtime orchestration.
Its purpose is to identify the dominant cause of the observed 16.7% qualified
recall before any behavioral repair is attempted.
