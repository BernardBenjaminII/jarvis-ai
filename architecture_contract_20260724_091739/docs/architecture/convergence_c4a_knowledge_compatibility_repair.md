# JARVIS Convergence C-4A — Knowledge Compatibility Repair

## Status

Certification repair and compatibility stabilization.

## Purpose

C-4 activated catalog grounding and exposed two integration mismatches:

1. `core.knowledge_catalog.database` required the historical optional
   `STRUCTURE_SQL` export even though the active schema no longer exports it.
2. C-1 and C-2 HTTP contracts required exact pre-grounding answer strings,
   although C-4 intentionally enriches synthesis input with grounding context.

C-4A repairs both boundaries without disabling knowledge grounding or changing
the production orchestration path.

## Canonical decisions

- Required Knowledge Catalog scripts remain mandatory.
- `STRUCTURE_SQL` is treated as an optional generation-specific extension.
- Catalog migrations remain idempotent.
- HTTP contracts validate stable answer prefixes and structured metadata.
- Production synthesis, routing, Director activation, and grounding remain live.

## Non-goals

C-4A does not add full-text retrieval, embeddings, admissibility assessment,
reasoning synthesis, acquisition execution, or a new Knowledge Catalog schema.
