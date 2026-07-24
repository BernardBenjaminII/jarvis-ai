# ADR-0016 — Knowledge Capability Ownership

## Status

Accepted

## Context

The JARVIS knowledge system has evolved through multiple implementation phases.

Current knowledge-related subsystems include:

- `knowledge_engine`
- `core/knowledge_catalog`
- `core/knowledge_graph`
- `core/knowledge_mapper`
- `core/semantic_digest`
- `dev/librarian`

A capability audit showed substantial overlap across acquisition, cataloging, classification, extraction, graphing, inspection, reading, search, and storage.

This creates risk of duplicated work and architectural drift.

## Decision

Define canonical owners for each knowledge capability.

Future work must extend the canonical owner unless an ADR explicitly changes ownership.

## Canonical Ownership

| Capability | Canonical Owner |
|---|---|
| Acquisition | `dev/librarian` |
| Discovery | `dev/librarian` |
| Normalization | `dev/librarian` |
| Inspection | `knowledge_engine` |
| Reading | `knowledge_engine` |
| Extraction | `knowledge_engine` |
| Chunking | `knowledge_engine` |
| Embedding | `knowledge_engine` |
| Catalog | `core/knowledge_catalog` |
| Classification | `core/knowledge_catalog` |
| Storage | `core/knowledge_catalog` |
| Search | `core/knowledge_catalog` |
| Graph | `core/knowledge_graph` |
| CKO | `dev/librarian` |

## Consequences

- `knowledge_engine` becomes the canonical ingestion mechanics layer.
- `core/knowledge_catalog` becomes the canonical semantic state and search layer.
- `core/knowledge_graph` becomes the canonical coverage and gap reasoning layer.
- `dev/librarian` remains the acquisition and discovery layer.
- `core/knowledge_mapper` becomes transitional.
- `core/semantic_digest` becomes experimental/transitional until folded into the canonical owner modules.

## Rule

No new knowledge subsystem may be created until the canonical owner has been checked first.

If a capability already has an owner, extend the owner instead of creating a parallel implementation.
