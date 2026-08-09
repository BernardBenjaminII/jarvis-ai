# Genesis X-A1.1 — SQLite Reliability and Resume Repair

## Mission

Repair X-A1 production reliability after the first 100-document scale canary
exposed a transient SQLite lock and stranded checkpoint states.

## Repairs

- switches the runtime catalog to WAL mode;
- sets a 30-second SQLite connection timeout;
- sets `PRAGMA busy_timeout=30000`;
- retries transient lock failures with bounded exponential backoff and jitter;
- recovers `EXTRACTING`, `EXTRACTED`, `CHUNKED`, and `WRITING` to `VALIDATED`;
- recovers `FAILED` records whose detail contains `database is locked`;
- drains or cancels outstanding futures when `--stop-on-error` is triggered;
- resets extracted-but-unwritten work to a resumable state;
- preserves per-document transactional writes;
- preserves the invariant `runtime_chunks == runtime_chunks_fts`.

## Recovery Semantics

The checkpoint does not persist extracted text or chunks. Therefore, incomplete
extraction-only states are reset to `VALIDATED` and safely re-extracted.

Committed runtime documents are not touched.

## SQLite Policy

```text
journal_mode       WAL
synchronous        NORMAL
connect timeout    30 seconds
busy_timeout       30,000 ms
retry attempts     6
initial backoff    100 ms
maximum backoff    5 seconds
```

## Operational Sequence

1. Install X-A1.1.
2. Run the state recovery command.
3. Confirm `CHUNKED` and lock-failed counts have returned to `VALIDATED`.
4. Run a new 100-document canary.
5. Scale only after the repaired canary passes.
