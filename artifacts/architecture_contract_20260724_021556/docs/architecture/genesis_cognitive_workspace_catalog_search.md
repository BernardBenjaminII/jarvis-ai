# Genesis III-A3 — Cognitive Workspace Catalog and Search

## Purpose

Genesis III-A3 makes persisted reasoning discoverable.

JARVIS can now inspect its cognitive history and locate workspaces by:

- objective or workspace identity;
- hypothesis, evidence, assumption, and question text;
- workspace lifecycle status;
- confidence range;
- unresolved-question state;
- assumption presence;
- update time;
- deterministic ordering and limits.

## Architectural boundary

The catalog operates over the repository contract introduced in Genesis III-A2.

It does not depend directly on SQLite.

This preserves the ability to replace the persistence layer without replacing
the catalog query model.

## Main contracts

### WorkspaceCatalogEntry

A compact searchable projection containing:

- identity;
- objective;
- lifecycle status;
- revision;
- timestamps;
- object counts;
- strongest hypothesis and confidence;
- normalized searchable text.

### WorkspaceQuery

A structured immutable query supporting:

- text terms;
- statuses;
- confidence bounds;
- unresolved-question filter;
- assumption filter;
- update-time bounds;
- sorting;
- result limits.

### CognitiveWorkspaceCatalog

Provides:

- complete catalog rebuilding;
- deterministic search;
- full-workspace retrieval;
- resumable-workspace discovery;
- blocked-workspace discovery;
- low-confidence discovery.

## Search semantics

Text search uses case-insensitive AND matching.

For example:

`meta quest spatial`

matches only entries containing all three terms somewhere in the normalized
workspace projection.

## Determinism

Every search has an explicit primary sort field and workspace identity as the
stable tie-breaker.

The same repository state and query therefore produce the same ordered result.

## Non-goals

This phase does not introduce:

- semantic vector search;
- fuzzy matching;
- full-text database indexes;
- cross-repository federation;
- automatic tagging;
- relevance scoring;
- background catalog materialization.

Those remain future optimization and intelligence phases.
