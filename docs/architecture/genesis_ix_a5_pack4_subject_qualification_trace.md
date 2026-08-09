# Genesis IX-A5 Pack 4 — Subject Qualification Trace

## Mission

Explain why the qualification subject component becomes zero or rejects
otherwise relevant evidence.

## Trace Flow

```text
Operator query
    ↓
query normalization and tokens
    ↓
expected subject candidates
    ↓
raw and qualified retrieval
    ↓
candidate subject metadata extraction
    ↓
taxonomy and alias comparison
    ↓
subject component and final score
    ↓
diagnosis
```

## Diagnoses

- `MISSING_SUBJECT_METADATA`
- `TAXONOMY_OR_ALIAS_MISMATCH`
- `SUBJECT_SCORING_DEFECT`
- `SUBJECT_SCORE_NOT_EXPOSED`
- `SUBJECT_MATCH_ACCEPTED`
- `SUBJECT_MATCH_PARTIAL_OR_REJECTED`

## Outputs

The report includes:

- query and token traces;
- detected query subjects;
- stored candidate subjects;
- candidate domain;
- exact and alias matches;
- overlap score;
- subject score;
- final score and threshold;
- decision;
- missing-metadata list;
- diagnosis counts;
- subject heatmap.

## Safety

Pack 4 is read-only. It does not modify catalog metadata, taxonomy files,
aliases, qualification weights, thresholds, retrieval, or runtime behavior.
