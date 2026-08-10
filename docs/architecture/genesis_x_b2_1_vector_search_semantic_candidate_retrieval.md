# Genesis X-B2.1 — Vector Search & Semantic Candidate Retrieval

## Objective

Genesis X-B2.1 activates the completed X-B1 semantic corpus as a searchable
retrieval substrate.

X-B1 answered whether the complete runtime corpus could be represented
semantically. X-B2.1 answers the next question:

> Given a natural-language query, can JARVIS retrieve the most semantically
> relevant persisted knowledge candidates with deterministic provenance?

## Scope

X-B2.1 provides:

- query embedding through the certified embedding provider,
- exact cosine similarity over canonical semantic vectors,
- exact cosine similarity over semantic fragment vectors,
- fixed-memory block streaming,
- global top-K candidate ranking,
- canonical versus fragment source identification,
- runtime chunk and document provenance,
- candidate text previews,
- read-only operation against both runtime and semantic databases,
- audit, status, query, and certification commands.

## Canonical safety

X-B2.1 performs no write operations against:

- `catalog.sqlite`
- `semantic_index.sqlite`

Both databases are opened in SQLite read-only/query-only mode.

## Retrieval contract

Each candidate includes:

- rank,
- cosine score,
- source type,
- runtime chunk ID,
- runtime document ID,
- canonical chunk UUID,
- optional fragment UUID,
- optional fragment index,
- document title,
- source file path,
- text preview.

## Exact search versus future ANN search

X-B2.1 intentionally establishes a correctness-first exact-search contract.
It scans vectors in bounded blocks and maintains a top-K heap.

This avoids prematurely binding the architecture to an ANN implementation.

A later X-B2 optimization pack may introduce HNSW, FAISS, sqlite-vector, or
another ANN backend while preserving the X-B2.1 result contract and using
exact X-B2.1 search as a quality oracle.

## Commands

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python

"$PYTHON_BIN" -m dev.run_genesis_x_b2_1 audit

"$PYTHON_BIN" -m dev.run_genesis_x_b2_1 query \
  --query "How do C++ iterators work?" \
  --top-k 10 \
  --scan-limit 25000

"$PYTHON_BIN" -m dev.run_genesis_x_b2_1 certify
```

Omit `--scan-limit` to perform a complete exact semantic search over the
selected scope.
