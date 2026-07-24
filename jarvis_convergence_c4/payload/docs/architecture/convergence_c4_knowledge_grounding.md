# JARVIS Convergence C-4 — Knowledge Grounding

## Purpose

C-4 connects the certified Executive Conversation and Director Activation path to the canonical Knowledge Catalog. It does not replace the catalog, source registry, evidence system, reasoning engine, or assimilation pipeline.

## Canonical flow

```text
Operator request
  -> objective compilation
  -> catalog grounding
  -> evidence records or explicit knowledge gaps
  -> capability routing and Director execution
  -> evidence-aware Executive synthesis
  -> response metadata with provenance and gaps
```

## Operational contracts

- Every compiled objective receives an independent catalog query.
- Retrieved records retain subject, source path, confidence, and assignment provenance.
- An empty or unavailable catalog creates an explicit `KnowledgeGap`; it never silently invents evidence.
- The live Knowledge Director uses the same catalog adapter as conversation grounding.
- `JARVIS_CATALOG_DB` may override the canonical catalog database path.
- Existing C-1 through C-3 behavior remains available when no grounding service is injected.

## Boundaries

C-4 retrieves metadata-level evidence from the existing catalog. Full-text chunk retrieval, embedding ranking, evidence admissibility assessment, and reasoning synthesis remain later convergence work or existing subsystems to be activated behind this stable contract.
