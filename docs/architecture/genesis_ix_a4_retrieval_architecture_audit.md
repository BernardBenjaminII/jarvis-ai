# Genesis IX-A4 — Retrieval Architecture Audit & Integration Readiness

## Mission

Inventory and certify existing retrieval assets before adding new retrieval
or grounded-answer code.

## Rule

> Reuse first. Replace second. Rewrite only as a last resort.

## Scope

The audit inventories conversation entry points, orchestration, grounding,
knowledge awareness, materialization, full-text search, chunks, embeddings,
vector and similarity code, ranking, evidence, sources, provenance, API
routes, Mission Control wiring, database tables, row counts, and live
dependency composition.

## Deliverables

- `docs/audits/genesis_ix_a4_retrieval_architecture.md`
- `docs/audits/genesis_ix_a4_retrieval_architecture.json`

IX-A4 is audit-first. It does not introduce another ranker, vector database,
query planner, or grounded-answer engine until the report proves that such a
capability is missing or inadequate.
