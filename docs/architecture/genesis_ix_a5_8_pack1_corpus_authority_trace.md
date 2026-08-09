# Genesis IX-A5.8 Pack 1 — Corpus Authority and Materialization Trace

## Mission

Determine which knowledge catalog is authoritative and trace the measurable
progression from catalog registration through runtime materialization, chunking,
FTS indexing, and retrieval readiness.

## Safety

This pack is read-only. It performs no migrations, writes, materialization,
chunking, indexing, or metadata changes.

## Authority Rules

Authority scoring favors:

- the configured `DEFAULT_CATALOG_DB`;
- populated runtime FTS;
- populated runtime documents;
- populated catalog registries;
- canonical catalog naming.

Backup naming is penalized.

## Pipeline Stages

The pack measures:

1. `documents`;
2. `knowledge_index`;
3. `library_catalog`;
4. `knowledge_classifications`;
5. `runtime_documents`;
6. `runtime_chunks`;
7. `runtime_chunks_fts`.

## Critical Metrics

- catalog base;
- runtime document count;
- materialization rate;
- unmaterialized object count;
- chunks per runtime document;
- FTS coverage of runtime chunks;
- first non-strong lineage edge.

## Decision Boundary

If runtime FTS covers existing runtime chunks but materialization coverage is
low, the next repair must target candidate selection and materialization
campaign execution—not FTS ranking or prompt construction.
