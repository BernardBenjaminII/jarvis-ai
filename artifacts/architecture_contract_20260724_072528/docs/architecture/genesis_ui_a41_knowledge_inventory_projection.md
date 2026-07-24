# Genesis UI-A4.1 — Knowledge Inventory Projection

## Purpose

UI-A4.1 creates the first canonical Executive projection of the JARVIS
knowledge estate.

The projection is intentionally observational. It reports the state of the
knowledge root and its SQLite stores without changing them.

## Architecture

```text
Knowledge filesystem and SQLite stores
                 │
                 ▼
     KnowledgeInventoryService
                 │
                 ▼
      KnowledgeProjectionProvider
                 │
                 ▼
        ProjectionRegistry
                 │
                 ▼
   ExecutiveProjectionService
                 │
                 ▼
        Mission Control API
```

## Inventory scope

The service reports:

- configured root
- root existence and readability
- database names and sizes
- database table names
- row counts per table
- total visible rows
- filesystem file count
- filesystem directory count
- filesystem byte count
- extension distribution
- top-level storage distribution
- scan truncation
- warnings and errors
- deterministic state fingerprint

## Read-only boundary

SQLite databases are opened with:

```text
mode=ro
```

UI-A4.1 does not:

- create databases
- migrate schemas
- modify records
- enqueue ingestion
- download sources
- create knowledge gaps
- execute research

## Performance boundary

The inventory is cached for a configurable TTL. Filesystem traversal has a
configurable maximum file count. This prevents the Mission Control projection
from becoming an unbounded request-time scan.

## Subsequent UI-A4 installments

- UI-A4.2 — Catalog Semantic Metrics
- UI-A4.3 — Assimilation Pipeline Projection
- UI-A4.4 — Domain Coverage and Knowledge Gaps
- UI-A4.5 — Knowledge Recommendations and UI binding
