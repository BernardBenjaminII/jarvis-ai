# Genesis IX-A4.3A — Certification Failure Analyzer

Reads `docs/audits/genesis_ix_a4_3/end_to_end_certification.json`, isolates failed checks, correlates them with the known trace, gap trace, grounded prompt, runtime snapshot, and metadata, then classifies each failure as:

```text
RUNTIME_BUG
CERTIFICATION_BUG
METADATA_MISMATCH
EXPECTED_BEHAVIOR
DATA_QUALITY
UNKNOWN
```

Outputs:

```text
docs/audits/genesis_ix_a4_3a/
    failure_analysis.json
    failure_analysis.md
    failure_classification_matrix.md
    minimal_repair_plan.md
```

The analyzer recommends the smallest justified repair and must not prescribe a runtime change when the evidence points to query-selection or metadata-adapter defects.
