# Genesis IX-A4.2A — Retrieval Pipeline Inventory

Audits the production retrieval subsystem before any new implementation is introduced.

The inventory covers Executive and conversation retrieval, catalog search, registry access, chunks, embeddings, semantic similarity, FTS, BM25, hybrid retrieval, reranking, citations, evidence, provenance, runtime materialization, caches, runtime dependency injection, and SQLite readers/writers.

Canonical analysis is limited to `core/` and `knowledge_engine/`. Tests, payloads, archives, artifacts, migration backups, Genesis snapshots, convergence trees, and architecture snapshots are excluded.

Outputs:

```text
docs/audits/retrieval_inventory/
    pipeline_inventory.json
    retrieval_graph.json
    runtime_inventory.md
    capability_matrix.md
    retrieval_graph.md
```
