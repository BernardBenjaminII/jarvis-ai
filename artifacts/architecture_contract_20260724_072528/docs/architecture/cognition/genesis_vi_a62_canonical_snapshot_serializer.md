# Genesis VI-A6.2 — Canonical Snapshot Serializer

**Status:** Implemented  
**Parent:** Genesis VI-A6 — Executive Persistence  
**Prerequisite:** Genesis VI-A6.1

## Constitutional Rule

> One executive state shall always serialize into one canonical byte
> representation.

## Purpose

VI-A6.2 converts immutable executive state into deterministic UTF-8 JSON bytes.
The resulting bytes are suitable for hashing, checkpoint storage, comparison,
replication, and future recovery.

## Canonical Rules

- JSON object keys are sorted.
- No insignificant whitespace is emitted.
- UTF-8 is mandatory.
- Naive datetimes are rejected.
- Datetimes are normalized to UTC with microsecond precision.
- Enumeration identity and value are preserved.
- Dataclass identity and fields are preserved.
- Tuple and set semantics are explicitly tagged.
- Set members are sorted by canonical representation.
- Mapping keys must be strings.
- NaN and infinity are rejected.
- SHA-256 is calculated over the exact emitted bytes.

## Public API

- `CanonicalSnapshotSerializer`
- `SerializedSnapshot`
- `SerializationError`
- `CanonicalizationError`
- `to_canonical_value`

## Boundary

The serializer performs no file or database I/O. Checkpoint persistence belongs
to VI-A6.3.

## Next Milestone

**Genesis VI-A6.3 — Checkpoint Store and Integrity Verification**
