# Genesis IX-A4.1B Pack 1 — Retrieval Audit Engine

## Mission

Discover and classify production retrieval and runtime assets before
canonicalization or behavioral change.

## Scope

Pack 1 inventories:

- search and retrieval functions;
- ranking, similarity, vector, and embedding functions;
- retrieval-related classes and imports;
- live retrieval ownership;
- knowledge database tables, indexes, and row counts;
- SQL readers and writers;
- canonical, dormant, and auxiliary implementations.

## Canonical Boundary

Canonical source inspection includes:

```text
core/
knowledge_engine/
```

Auxiliary evidence may be collected from:

```text
dev/
```

Historical payloads, snapshots, archives, artifacts, tests, and migration
backups are excluded from canonical ownership.

## Deliverables

```text
docs/audits/genesis_ix_a4_1b_pack1/
    retrieval_runtime_inventory.json
    retrieval_runtime_inventory.md
```

Pack 2 will consume this machine-readable census to generate the runtime graph,
component matrix, duplicate report, and canonicalization recommendations.
