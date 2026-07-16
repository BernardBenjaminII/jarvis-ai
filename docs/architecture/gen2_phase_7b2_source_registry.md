# JARVIS Gen 2 Phase VII-B2

## Persistent Source Registry

Phase VII-B2 introduces persistent lifecycle management for sources that have
already passed Phase VII-B1 admission.

## Architectural Rule

The registry may consume accepted `AdmissionDecision` objects from
`knowledge_engine.acquisition_control`.

It must not bypass admission policy or import the frozen
`knowledge_engine.acquisition` implementation.

## Responsibilities

- Persist admitted sources
- Assign stable registry identifiers
- Prevent duplicate registration by fingerprint
- Detect conflicting reuse of source IDs
- Track lifecycle state
- Preserve canonical location, trust tier, host, metadata, and admission time
- Expose deterministic statistics

## Lifecycle

```text
admitted -> active -> paused -> active
admitted -> retired
active -> retired
paused -> retired
retired -> terminal
```

## Non-Responsibilities

- No crawling
- No downloading
- No scheduling
- No retry logic
- No document assimilation
- No source truth evaluation

## Persistence

The initial implementation uses SQLite and creates a dedicated
`source_registry` table with unique constraints on:

- `source_id`
- `fingerprint`

## Completion Criteria

- Accepted sources persist successfully
- Review/rejected decisions cannot register
- Duplicate fingerprints are idempotent
- Source ID conflicts are rejected
- Lifecycle transitions are enforced
- Registry statistics are correct
- VII-B1 regression remains green
