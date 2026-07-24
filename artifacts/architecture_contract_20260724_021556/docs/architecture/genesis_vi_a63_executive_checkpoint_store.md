# Genesis VI-A6.3 — Executive Checkpoint Store

**Status:** Certified implementation candidate  
**Subsystem:** Executive Persistence  
**Schema:** `jarvis.executive.checkpoint@1`

## Constitutional law

> Every certified executive state shall be recoverable from an immutable
> checkpoint whose provenance, integrity, ordering, and parentage are
> independently verifiable.

## Purpose

Genesis VI-A6.3 introduces the first durable executive persistence backend.
It stores canonical snapshot bytes without interpreting executive cognition,
reasoning, planning, or mission semantics.

The checkpoint store is intentionally filesystem-based and database-free.
Every durable record remains inspectable, portable, and replaceable through
the repository boundary.

## Architecture

```text
Executive Session
        |
        v
Canonical Snapshot Serializer
        |
        v
Checkpoint Repository
        |
        v
Atomic File Storage
        |
        v
Filesystem
```

## Runtime layout

```text
runtime/executive/checkpoints/
    sessions/
        <session-id>/
            00000001.chk
            00000002.chk
            index.json
    archive/
        <session-id>/
    locks/
        <session-id>.lock
```

## Public responsibilities

### `storage.py`

- root-confined path resolution
- atomic binary replacement
- bounded binary reads
- directory synchronization where supported
- portable advisory lock files

### `checkpoint.py`

- immutable checkpoint records
- canonical wire encoding
- payload SHA-256 verification
- checkpoint manifest SHA-256 verification
- parent checkpoint linkage
- deterministic checkpoint identity

### `repository.py`

- append-only save
- exact load
- latest checkpoint lookup
- ordered history enumeration
- parent-chain verification
- session archival

## Stability rules

1. The Executive never writes checkpoint files directly.
2. Existing checkpoint records are never overwritten.
3. Sequence numbers begin at one and cannot contain gaps.
4. The first checkpoint uses the all-zero parent digest.
5. Every later checkpoint names the digest of its immediate predecessor.
6. Integrity is verified when records are loaded.
7. Storage backends may change without changing executive callers.

## Deferred to later phases

- VI-A6.4: full integrity scanning and quarantine
- VI-A6.5: recovery policy and session restoration
- VI-A6.6: deterministic replay
- VI-A6.7: schema migration
- VI-A6.8: persistence certification authority
