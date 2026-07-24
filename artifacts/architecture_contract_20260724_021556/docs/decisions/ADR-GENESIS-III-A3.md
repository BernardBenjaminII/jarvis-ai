# ADR — Add a Repository-Agnostic Cognitive Workspace Catalog

**Status:** Accepted  
**Milestone:** Genesis III-A3

## Context

Genesis III-A2 made cognitive workspaces durable, but persistence alone does
not make reasoning history usable.

JARVIS must be able to locate active, blocked, low-confidence, historical, and
topic-related workspaces without exposing callers to storage implementation
details.

## Decision

Introduce a repository-agnostic cognitive workspace catalog with:

- immutable catalog entries;
- immutable structured queries;
- deterministic text and metadata filters;
- stable ordering;
- convenience queries for resumable, blocked, and low-confidence workspaces.

The first implementation rebuilds its projection from repository state for each
query.

## Rationale

A projection-first catalog provides a clear domain contract before introducing
database-specific indexes or semantic retrieval.

This keeps correctness and determinism ahead of optimization.

## Consequences

### Positive

- Persisted reasoning becomes discoverable.
- The executive layer can resume relevant work.
- Search behavior is deterministic and testable.
- Storage remains replaceable.
- Future full-text or vector indexes can implement the same query boundary.

### Negative

- Rebuilding the catalog is linear in repository size.
- Text search is lexical rather than semantic.
- Large deployments will require a materialized index later.

## Deferred decisions

- SQLite FTS;
- vector similarity;
- relevance scoring;
- automatic workspace labels;
- cross-device catalog synchronization.
