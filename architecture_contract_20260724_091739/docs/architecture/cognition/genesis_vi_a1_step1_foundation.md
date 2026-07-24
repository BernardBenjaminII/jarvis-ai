# Genesis VI-A1 Step 1 — Executive Cognition Contracts

**Status:** Implemented  
**Scope:** Foundational contracts only  
**Package:** `core.cognition`

## Purpose

Step 1 establishes the immutable vocabulary and data contracts required by the
Genesis VI executive cognition kernel.

This increment intentionally contains no state machine, working-memory manager,
attention engine, cognition cycle, model integration, planning integration, or
execution integration.

## Included

- canonical cognition enumerations;
- canonical cognition exceptions;
- immutable memory-entry contracts;
- immutable attention contracts;
- immutable state-transition contracts;
- immutable cognitive-event contracts;
- immutable executive-context snapshots;
- stable package exports;
- unit and structural verification.

## Architectural Boundary

`core.cognition` may depend only on Python's standard library during Step 1.

It must not depend on:

- model providers;
- retrieval systems;
- reasoning systems;
- planners;
- execution systems;
- network clients;
- user-interface frameworks.

## Determinism

The contracts provide deterministic:

- enum values;
- normalized attention-reason ordering;
- metadata-key ordering;
- immutable tuples;
- immutable mapping views.

Timestamps are observational metadata and are not considered deterministic
identity.

## Deferred to Step 2

Step 2 will introduce bounded working memory with deterministic admission,
ordering, lookup, update, removal, replacement, and eviction behavior.
