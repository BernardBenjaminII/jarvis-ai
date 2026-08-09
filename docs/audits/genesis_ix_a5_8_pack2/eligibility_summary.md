# Genesis IX-A5.8 Pack 2 — Materializer Eligibility Audit

**Status:** **FAILED**
**Classification:** **ELIGIBLE_CORPUS_NOT_SELECTED**

## Summary

- Candidate records: **90,003**
- Runtime documents: **69**
- Already materialized: **13**
- Eligible but not selected: **89,283**
- Eligible selection rate: **0.01%**
- Missing sources: **0**
- Unsupported: **702**
- Containers/archives: **5**
- Failures: **0**

## Disposition Counts

- `ALREADY_MATERIALIZED`: **13**
- `CONTAINER_OR_ARCHIVE`: **5**
- `ELIGIBLE_NOT_SELECTED`: **89,283**
- `UNSUPPORTED_MEDIA_TYPE`: **702**

## Recommendations

- Repair or expand materializer candidate selection before changing retrieval ranking.
- Run a bounded materialization campaign against ELIGIBLE_NOT_SELECTED records.
- Add extractors only for high-volume unsupported formats proven valuable.
- Preserve split authority: inventory metadata and runtime retrieval have different canonical stores.
