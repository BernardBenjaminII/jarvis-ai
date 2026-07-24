# Genesis VI-A6.8 Part A — Executive Timeline Repository Foundation

**Status:** Implemented  
**Depends on:** Genesis VI-A6.7  
**Next:** Genesis VI-A6.8 Part B — Query and Certification

## Purpose

Part A gives the authoritative Executive Timeline durable, append-only storage.
The VI-A6.7 Timeline Engine remains the sole creator and chronological authority
for events. The repository accepts only already-certified `TimelineEvent`
instances and owns persistence, loading, deterministic indexes, statistics, and
independent repository verification.

## Storage format

The initial backend is canonical UTF-8 JSON Lines:

```text
<repository-root>/executive.timeline.jsonl
```

Each line contains one complete event envelope and ends with one newline. The
storage adapter supports append and sequential read only. It exposes no update,
delete, truncate, or archive operation.

## Responsibilities

```text
Timeline Engine (VI-A6.7)
        │ creates immutable events
        ▼
Executive Timeline Repository
        ├── canonical serializer
        ├── append-only storage
        ├── deterministic indexes
        ├── session and mission loading
        ├── repository statistics
        └── independent integrity verification
```

## Invariants

1. Persisted sequence begins at one and remains contiguous.
2. Each event fingerprint verifies against canonical event material.
3. Each event links to the immediately preceding event fingerprint.
4. Parent references point only to earlier persisted events.
5. Event IDs remain unique.
6. The repository never edits or deletes history.
7. Indexes are deterministic derivatives of persisted events.
8. Reloading the repository reconstructs the same immutable events.

## Deliberate exclusions

Part A does not introduce the general query language, pagination, replay,
background event dispatch, SQLite, or Mission Control integration. Those remain
outside this foundation so persistence can be certified independently.
