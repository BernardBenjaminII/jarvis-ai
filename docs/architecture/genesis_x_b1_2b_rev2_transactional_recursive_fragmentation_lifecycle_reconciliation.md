# Genesis X-B1.2b Revision 2 — Transactional Recursive Fragmentation & Lifecycle Reconciliation

This revision repairs the recursive-fragment identity defect caused by the legacy
`UNIQUE(runtime_chunk_id, fragment_index)` constraint.

## Schema

The semantic fragment table is rebuilt transactionally with:

- `fragment_uuid` primary key
- `UNIQUE(runtime_chunk_id, fragment_path)`
- parent/depth/path lineage retained
- existing rows preserved

## Transactional subdivision

A leaf is superseded only after all replacement children are inserted and
verified inside the same transaction. Any failure rolls back, leaving the source
leaf active.

## Reconciliation

The repair pass detects:

- `SUPERSEDED_CONTEXT` rows with zero children
- `REJECTED_CONTEXT` active leaves

Orphaned superseded rows are restored to `RETRY`. Terminal context leaves are
requeued for deeper transactional subdivision.

## Certification

Requires zero orphaned superseded fragments, zero unresolved fragmented parents,
zero incomplete leaves, zero terminal context rejections, and vectors for every
complete active leaf.
