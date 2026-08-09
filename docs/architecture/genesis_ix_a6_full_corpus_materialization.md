# Genesis IX-A6 — Full Corpus Materialization Campaign

## Mission

Safely materialize the eligible knowledge corpus into runtime documents,
runtime chunks, and SQLite FTS using bounded, resumable batches.

## Operational Safety

Installation does not execute the full campaign.

The campaign must be explicitly prepared, inspected through a dry run, and then
started with the `execute` command.

## Workflow

```text
eligible catalog candidates
    ↓
checkpoint registration
    ↓
bounded batch selection
    ↓
source validation
    ↓
existing RuntimeKnowledgeMaterializer
    ↓
runtime_documents
    ↓
runtime_chunks
    ↓
runtime_chunks_fts
    ↓
batch certification
    ↓
checkpoint and resume
```

## Checkpointing

Campaign state is stored separately from the production catalog:

```text
.runtime/materialization/genesis_ix_a6_campaign.sqlite
```

The checkpoint tracks:

- candidate identity;
- path and extension;
- disposition;
- attempt count;
- batch membership;
- timestamps;
- failure details;
- campaign events.

## Execution Gates

### Prepare

Discovers supported, readable, non-empty files not already represented in
`runtime_documents`.

### Dry Run

Validates a bounded candidate batch without invoking the materializer.

### Execute

Materializes a bounded batch and checks runtime document, chunk, and FTS deltas.

### Resume

Running `execute` again continues with remaining `PENDING` candidates.

## Integrity Rules

- The runtime catalog is changed only by the existing canonical materializer.
- Runtime chunk and FTS deltas must match.
- A runtime document with no chunks is classified as failed extraction.
- Failed candidates remain checkpointed for review.
- Retry of failures requires an explicit flag.
- Full-corpus execution is never triggered during installation.

## Recommended Initial Production Sequence

```bash
python -m dev.run_genesis_ix_a6_materialization prepare

python -m dev.run_genesis_ix_a6_materialization   dry-run   --batch-size 25   --max-batches 1

python -m dev.run_genesis_ix_a6_materialization   execute   --batch-size 10   --max-batches 1   --stop-on-error
```

After validating the first production batch, increase batch size gradually.
