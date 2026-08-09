# Genesis X-A1 — Production Materialization Engine

## Mission

Materialize the full eligible knowledge corpus with parallel extraction,
serialized SQLite writes, durable stage checkpoints, bounded batches, resume,
throughput reporting, ETA, quarantine, and FTS integrity verification.

## Architecture

```text
checkpointed queue
    ↓
parallel extraction workers
    ↓
deterministic chunk preparation
    ↓
single serialized SQLite writer
    ↓
runtime_documents
    ↓
runtime_chunks
    ↓
runtime_chunks_fts
    ↓
integrity verification
```

## Durable States

`DISCOVERED`, `VALIDATED`, `EXTRACTING`, `EXTRACTED`, `CHUNKED`, `WRITING`,
`COMPLETE`, `SKIPPED`, `FAILED`, and `QUARANTINED`.

## Safety

Installation does not start materialization. Execution requires an explicit
`execute` command. The checkpoint database is separate from the production
catalog. Each document write is one SQLite transaction. Chunk and FTS deltas
must match.
