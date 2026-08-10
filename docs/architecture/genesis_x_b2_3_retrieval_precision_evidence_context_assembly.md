# Genesis X-B2.3 — Retrieval Precision, Evidence Expansion & Context Assembly

## Objective

X-B2.2 proved that hybrid reranking can substantially improve semantic candidate
quality. X-B2.3 turns ranked candidates into a bounded evidence package suitable
for downstream reasoning.

## Pipeline

```text
Query
  |
  v
X-B2.2 hybrid retrieval
  |
  v
Precision gate
  |
  v
Strong anchors
  |
  +--> neighboring canonical chunks
  |
  v
Document-aware evidence pool
  |
  v
Redundancy suppression
  |
  v
Bounded context selection
  |
  v
Evidence bundle
```

## Precision gate

A candidate must satisfy:

- minimum hybrid score,
- minimum semantic score,
- at least one lexical or title concept signal.

This prevents high-semantic but conceptually weak candidates from consuming
reasoning context.

## Neighbor expansion

Accepted anchors can expand into nearby canonical chunks from the same document.
This provides explanatory continuity around a highly relevant hit.

Neighbors are explicitly labeled as supporting context rather than independent
semantic anchors.

## Redundancy suppression

Evidence is suppressed when:

- normalized fingerprints match exactly,
- token overlap exceeds the configured threshold,
- the per-document evidence budget is exhausted.

## Bounded context

The assembler enforces:

- maximum evidence items,
- maximum total characters,
- maximum items per document.

The output is deterministic and provenance-preserving.

## Safety

Both runtime and semantic databases remain read-only.
