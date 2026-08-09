# Genesis X-B1.1 — Semantic Corpus Index & Chunk Identity Bridge

## Mission

Create the semantic counterpart to the certified FTS corpus without modifying
`runtime_chunks` or the existing X-B/X-B1 baseline.

## Identity Bridge

Every runtime chunk receives a deterministic UUIDv5 derived from:

- runtime document ID
- runtime chunk ID
- content SHA-256

The mapping is stored separately in `semantic_index.sqlite`.

## Vector Store

Vectors are stored as compact float32 BLOBs, not JSON:

- runtime chunk ID
- stable chunk UUID
- provider
- model
- dimensions
- vector BLOB
- vector SHA-256

## Campaign

Embedding is resumable through `embedding_campaign`.

`prepare` registers all runtime chunks but does not embed them.

`embed --limit N` performs a bounded batch through local Ollama.

The default model is `mxbai-embed-large`.

## Search

X-B1.1 includes exact cosine search over whatever vectors have been built.
This is intended for canary validation and coverage certification.

A production ANN index is deliberately deferred until vector dimensions,
coverage, model, throughput, and storage size have been measured.

## Certification

Semantic retrieval cannot claim full certification merely because the table
exists.

- `EXCELLENT_FOUNDATION_PARTIAL_COVERAGE`: bridge complete, vectors > 0.
- `EXCELLENT_FULL_COVERAGE`: bridge and vectors cover every runtime chunk.
