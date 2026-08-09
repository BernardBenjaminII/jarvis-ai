# Genesis IX-A5.8 Pack 1 — Corpus Drop-Off

- Catalog base: **90,003**
- Runtime documents: **69**
- Unmaterialized catalog objects: **89,934**
- Materialization rate: **0.08%**
- Runtime chunks: **4,674**
- Chunks per runtime document: **67.74**
- Runtime FTS rows: **4,674**
- FTS chunk coverage: **100.00%**

## Recommendations

- Audit the materializer candidate selection and campaign history; the authoritative catalog is severely undermaterialized.
- Do not tune FTS ranking until runtime document coverage is expanded.
- FTS coverage of existing runtime chunks is healthy; focus on upstream materialization coverage.
- Inspect the first non-strong lineage edge: physical_catalog_registry -> search_metadata_registry.
