# Phase X-C2 — Semantic Articulation and Context Assembly

## Status

Implemented as an additive cognitive-representation milestone.

## Purpose

Phase X-C1 converts source material into immutable structural segments.
Phase X-C2 converts those segments into coherent semantic units and bounded
context packages suitable for later reasoning integration.

```text
source
  ↓
X-C1 segmentation
  ↓
X-C2 semantic articulation
  ↓
X-C2 context assembly
  ↓
future X-C3 cognitive interpretation
  ↓
reasoning
```

## Semantic articulation

`SemanticArticulator` applies deterministic grouping rules:

1. Headings establish active section titles.
2. Adjacent prose segments form paragraphs.
3. Adjacent bullet segments form lists.
4. List/prose transitions close the active unit.
5. Character limits split units deterministically.
6. Every unit retains all contributing segment identities and provenance.

The articulator accepts segment-like objects or mappings. This compatibility
boundary keeps X-C2 additive and avoids rewriting X-C1 contracts.

## Context assembly

`ContextAssembler` converts ordered articulated units into a `ContextWindow`
under explicit character and unit budgets.

The result records:

- included units;
- omitted units;
- truncation state;
- source segment identities;
- unit fingerprints;
- context fingerprint.

## Determinism

Equivalent input and policy produce identical unit ordering, identities,
fingerprints, context text, omissions, and context fingerprints. No timestamps,
network calls, database access, or model calls occur.

## Boundaries

Phase X-C2 does not retrieve knowledge, call an LLM, generate hypotheses,
change reasoning confidence, create missions, execute tools, authorize actions,
or change the API/UI.

## Next phase

Phase X-C3 should add deterministic cognitive interpretation over
`ContextWindow` objects: claims, questions, assumptions, constraints, entities,
relationships, and requested outcomes. Execution authority remains excluded.
