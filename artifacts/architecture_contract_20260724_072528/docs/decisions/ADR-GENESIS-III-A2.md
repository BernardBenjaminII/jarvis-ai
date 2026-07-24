# ADR — Persist Cognitive Workspaces Through a Repository Boundary

**Status:** Accepted  
**Milestone:** Genesis III-A2

## Context

Genesis III-A1 created immutable cognitive workspaces, but they existed only
in process memory.

JARVIS requires reasoning continuity across sessions and restarts without
coupling the domain model directly to a specific database.

## Decision

Introduce:

- a repository protocol;
- a canonical versioned JSON codec;
- a SQLite repository implementation;
- optimistic revision protection.

The domain model remains persistence-agnostic.

## Rationale

SQLite is selected for the first implementation because it is:

- local-first;
- transactional;
- cross-platform;
- available through Python's standard library;
- suitable for deterministic verification;
- easy to migrate later behind the repository boundary.

## Consequences

### Positive

- Active reasoning survives restart.
- Persistence remains replaceable.
- Stale writers are detected.
- Workspace payloads are portable and inspectable.
- No new third-party dependency is required.

### Negative

- SQLite is not a distributed coordination system.
- Serialized payload migrations must be governed.
- Large-scale search requires a future index.
