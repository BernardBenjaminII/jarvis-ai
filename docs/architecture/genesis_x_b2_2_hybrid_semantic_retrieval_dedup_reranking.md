# Genesis X-B2.2 — Hybrid Semantic Retrieval, Deduplication & Relevance Reranking

## Objective

X-B2.1 demonstrated that JARVIS can retrieve semantically relevant candidates
from the X-B1 vector corpus. The first canary also exposed three quality issues:

1. semantically adjacent false positives can outrank conceptually exact results,
2. repeated copies of the same passage consume multiple ranking positions,
3. canonical and fragment evidence compete without higher-level consolidation.

X-B2.2 introduces a correctness-oriented reranking layer over the X-B2.1
candidate contract.

## Pipeline

```text
Query
  |
  +--> Query-term analysis
  |
  +--> X-B2.1 semantic candidate pool
             |
             v
       lexical agreement
       title agreement
       exact passage dedup
       source-family diversity
       canonical/fragment competition
             |
             v
       hybrid relevance score
             |
             v
           Top K
```

## Hybrid score

The initial deterministic score is:

```text
0.64 semantic
0.24 lexical
0.12 title
- source diversity penalty
```

This weighting keeps the semantic model primary while allowing exact concept
agreement to defeat semantically adjacent false positives.

## Deduplication

Candidates with normalized-equivalent evidence text collapse to one result.
Repeated copies from the same source family remain eligible but receive an
increasing diversity penalty.

## Safety

X-B2.2 is read-only with respect to both:

- canonical runtime catalog
- semantic index

No vector rebuilding or corpus mutation is performed.
