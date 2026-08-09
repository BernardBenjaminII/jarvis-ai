# Genesis X-B1 — Hybrid Retrieval & Semantic Ranking Foundation

## Mission

Improve retrieval quality without replacing or mutating the proven FTS5/BM25
baseline.

## Channels

1. FTS5/BM25 lexical retrieval
2. query/entity analysis
3. title/path metadata weighting
4. authority hints
5. optional semantic channel when a compatible existing `chunk_embeddings`
   store is present
6. reciprocal-rank fusion
7. duplicate suppression
8. per-document diversity control

X-B1 does not generate embeddings. It audits the existing semantic substrate and
uses it only when compatible. If semantic vectors are absent or incompatible,
the hybrid path remains valid as lexical + metadata + diversity fusion.

## Comparison Principle

X-B remains the baseline.
X-B1 runs side-by-side and reports old-vs-new ranking behavior.
