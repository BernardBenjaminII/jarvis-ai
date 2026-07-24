# Genesis III-A2 — Persistent Cognitive Workspace Repository

## Purpose

Genesis III-A2 gives JARVIS durable working memory for active reasoning.

A cognitive workspace can now survive process termination, machine restart,
or session changes without weakening the immutable model introduced in III-A1.

## Architecture

The phase introduces three layers:

1. `CognitiveWorkspaceRepository`
   - persistence protocol;
   - storage-independent contract.

2. `CognitiveWorkspaceCodec`
   - canonical JSON serialization;
   - explicit schema version;
   - deterministic encoding.

3. `SQLiteCognitiveWorkspaceRepository`
   - local durable storage;
   - optimistic revision checks;
   - stable workspace identity lookup;
   - ordered workspace enumeration;
   - protected deletion.

## Concurrency model

The repository uses optimistic concurrency.

A writer may provide `expected_revision`.

The save succeeds only when the stored revision matches the expected revision
and the replacement workspace advances the revision.

This prevents stale reasoning processes from silently overwriting newer state.

## Storage model

The SQLite table stores:

- workspace identity;
- revision;
- status;
- objective;
- canonical JSON payload;
- creation and update timestamps.

The complete immutable workspace remains the authoritative stored object.

## Non-goals

This phase does not provide:

- distributed locking;
- multi-host replication;
- workspace search;
- event streaming;
- automatic checkpointing;
- encryption at rest;
- retention policy;
- background recovery.

Those capabilities remain subsequent milestones.
