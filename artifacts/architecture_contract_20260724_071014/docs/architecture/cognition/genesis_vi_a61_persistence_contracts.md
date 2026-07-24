# Genesis VI-A6.1 — Persistence Contracts

**Status:** Implemented  
**Parent phase:** Genesis VI-A6 — Executive Persistence  
**Package:** `core.executive.persistence`

## Constitutional Rule

> Durable executive state must cross process boundaries through explicit,
> versioned, immutable, and integrity-addressed contracts.

## Purpose

VI-A6.1 establishes the persistence vocabulary used by every later A6
milestone. It introduces no storage backend and performs no serialization.

This separation prevents file formats, databases, or operating-system details
from defining the executive's durable state model.

## Contracts

- `SchemaIdentity`
- `IntegrityMetadata`
- `PersistenceEnvelope`
- `CheckpointDescriptor`
- `MigrationPath`
- `RecoveryRequest`

## Enumerations

- `PersistenceRecordKind`
- `PersistenceIntegrityStatus`
- `CheckpointReason`

## Fixed Schema Identity

```text
jarvis.executive.persistence@1
```

The schema name remains stable. Future incompatible representations increment
the integer version and require an explicit `MigrationPath`.

## Integrity Boundary

VI-A6.1 standardizes SHA-256 metadata but does not calculate or validate a
payload digest. Canonical serialization and digest calculation belong to
VI-A6.2.

## Explicit Non-Goals

VI-A6.1 does not:

- serialize executive sessions;
- write files or databases;
- calculate payload hashes;
- create checkpoints;
- restore sessions;
- replay events;
- execute migrations.

## Next Milestone

**Genesis VI-A6.2 — Canonical Snapshot Serializer**

A6.2 will convert the certified VI-A5 `ExecutiveSessionSnapshot` aggregate into
a deterministic, versioned byte representation suitable for integrity hashing
and later checkpoint storage.
