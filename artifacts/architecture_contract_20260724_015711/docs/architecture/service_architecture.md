# Knowledge Engine Service Architecture

**Status:** Active

**Phase:** Phase III-D — Service Consolidation

---

# Purpose

The Service Layer is the public API of the Knowledge Engine.

External systems should never directly import internal implementation modules.

Instead they should communicate through the canonical services.

---

# Architecture

```text
Workflow
    ↓
Knowledge Services
    ↓
Knowledge Engine
    ↓
Persistence
```

---

# Public Services

- ExtractionService
- ChunkingService
- EmbeddingService
- WorkflowRegistryService
- RetrievalService
- GraphService

---

# Responsibilities

## Workflow

Responsible only for orchestration.

Must never implement business logic.

---

## Services

Responsible for exposing stable APIs.

Services delegate to the production implementation.

---

## Knowledge Engine

Responsible for actual document processing.

Contains:

- Extraction
- Chunking
- Embeddings
- Registry
- Retrieval
- Knowledge Graph

---

## Persistence

Responsible for SQLite and vector storage.

Never called directly from workflows.

---

# Architecture Rule

Workflow Stages

↓

Services

↓

Knowledge Engine

↓

Persistence

No layer may bypass the one beneath it.
