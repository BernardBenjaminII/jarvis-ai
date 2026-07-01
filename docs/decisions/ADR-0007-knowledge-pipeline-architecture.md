# ADR-0007: Knowledge Pipeline Architecture

**Status:** Accepted  
**Date:** 2026-07-01

## Context

JARVIS is evolving from a local AI assistant into a platform that maintains and reasons over a large offline Knowledge Warehouse.

The Knowledge Warehouse may eventually contain hundreds of thousands or millions of files. A simple RAG pipeline that extracts all text and searches everything directly will not scale well.

## Decision

The Knowledge Engine will use a staged pipeline:

1. Discovery
2. Catalog
3. Inspection
4. Structure Extraction
5. Knowledge Index
6. Reading Queue
7. Text Extraction
8. Chunking
9. Concept Graph
10. Embeddings
11. Retrieval
12. LLM Answering

Each stage must be independently testable, resumable, and replaceable.

## Principle

The filesystem stores documents.  
The database stores knowledge.

## Consequences

Positive:

- JARVIS can reason over structure before reading full text.
- The Knowledge Index becomes a fast card catalog.
- Expensive processing can be prioritized.
- Future retrieval can combine index, structure, text, concepts, and embeddings.

Negative:

- More tables and stages are required.
- Implementation must be disciplined.
- More CLI and Doctor checks are needed.
