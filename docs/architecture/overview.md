# JARVIS Knowledge Engine Architecture

**Version:** 1.0 (Draft)

---

# Purpose

The Knowledge Engine is responsible for ingesting, organizing, indexing, retrieving, and maintaining every piece of knowledge available to JARVIS regardless of its origin.

It is **not** a RAG implementation.

RAG is only one capability provided by the Knowledge Engine.

The Knowledge Engine becomes one of the core subsystems of JARVIS alongside:

* Memory
* Identity
* Runtime
* Tool Execution
* Model Routing

---

# Guiding Philosophy

Repository contains behavior.

Runtime contains state.

```
Repository
    ↓
Python code
Architecture
Configuration
Interfaces

Runtime
    ↓
Knowledge
Embeddings
Indexes
Catalog
Memory
Logs
Cache
```

The repository should remain portable.

The runtime should remain replaceable.

---

# Design Principles

## Single Responsibility

Every component owns one responsibility.

No class should perform multiple unrelated tasks.

---

## Interface First

JARVIS communicates with interfaces rather than implementations.

Examples:

```
KnowledgeService

KnowledgeProvider

KnowledgeAsset
```

The rest of JARVIS should never know whether knowledge is stored in:

* FAISS
* Chroma
* SQLite
* Ollama embeddings
* OpenAI embeddings

Those are implementation details.

---

## Provider-Based Architecture

Knowledge originates from providers.

Examples:

* PDF
* Filesystem
* Git Repository
* Markdown
* Email
* Calendar
* Conversation
* Web
* API
* DoomsdayDisk

Every provider implements the same interface.

```
scan()

ingest()

update()
```

Providers return KnowledgeAssets.

---

# Runtime Layout

```
knowledge/

    catalog.sqlite

    providers.sqlite

    taxonomy.sqlite

    cache/

    chunks/

    embeddings/

    indexes/

    manifests/
```

---

## catalog.sqlite

Master inventory of every KnowledgeAsset.

Stores:

* asset id
* checksum
* source
* collection
* timestamps
* metadata
* embedding reference

---

## providers.sqlite

Tracks provider state.

Stores:

* provider name
* enabled
* last scan
* last update
* asset count
* synchronization status

---

## taxonomy.sqlite

Defines logical organization.

Examples:

* collections
* categories
* tags
* relationships

---

## chunks/

Chunked text awaiting embedding.

---

## embeddings/

Embedding cache.

---

## indexes/

Vector indexes.

Initially FAISS.

Future implementations should be replaceable.

---

## manifests/

Incremental synchronization state.

Allows efficient rescanning.

---

# Core Objects

## KnowledgeAsset

Represents every searchable unit of knowledge_engine.

Examples:

* PDF page
* Source code
* Git commit
* Markdown
* Conversation
* Email
* Note
* Manual
* API response

Fields include:

* id
* checksum
* asset_type
* collection
* source
* origin
* metadata
* content
* created_at
* modified_at
* embedding_id

---

## KnowledgeProvider

Responsible for discovering knowledge_engine.

Functions:

```
scan()

ingest()

update()
```

Never performs searching.

Never performs prompting.

---

## KnowledgeService

Public API exposed to JARVIS.

Responsibilities:

* initialize
* search
* ingest
* collections
* statistics

No implementation details exposed.

---

## KnowledgeEngine

Internal orchestration layer.

Responsible for coordinating:

* providers
* catalog
* chunking
* embeddings
* indexing
* retrieval
* taxonomy

Invisible to the rest of JARVIS.

---

# Knowledge Flow

```
Filesystem

        │

        ▼

Knowledge Provider

        │

        ▼

KnowledgeAsset

        │

        ▼

Catalog

        │

        ▼

Chunk Manager

        │

        ▼

Embedding Engine

        │

        ▼

Vector Index

        │

        ▼

Search Engine

        │

        ▼

KnowledgeService

        │

        ▼

Prompt Builder

        │

        ▼

LLM
```

---

# Query Flow

```
User

    │

Intent Classification

    │

Need Knowledge?

    │

KnowledgeService.search()

    │

Retrieved Assets

    │

Prompt Builder

    │

LLM

    │

Response
```

---

# Collections

Collections provide logical separation.

Examples:

```
jarvis

doomsdaydisk

aviation

school

military

personal

books

bug_bounty
```

Collections are independent.

Searching may target one or multiple collections.

---

# Future Expansion

Planned providers:

* PDF
* Markdown
* Plain Text
* Source Code
* Git
* Email
* Calendar
* Conversation
* Image OCR
* Audio Transcript
* Web
* REST APIs

---

# Long-Term Goal

The Knowledge Engine becomes the single source of truth for every piece of searchable information available to JARVIS.

Memory stores experience.

Knowledge stores facts.

Reasoning combines both.

The assistant should never care where knowledge originated.

It should only ask the Knowledge Service.

---

# Current Milestones

## Milestone 1

Architecture

* KnowledgeAsset
* KnowledgeProvider
* KnowledgeService
* Package structure

---

## Milestone 2

Provider Framework

* PDF provider
* Filesystem provider
* Markdown provider

---

## Milestone 3

Catalog

* catalog.sqlite
* provider registry
* checksum tracking

---

## Milestone 4

Chunking & Embeddings

* chunk manager
* embedding engine
* vector indexes

---

## Milestone 5

Retrieval

* semantic search
* metadata filtering
* citation generation

---

## Milestone 6

JARVIS Integration

* prompt builder
* `/ask`
* project indexing
* DoomsdayDisk integration
* memory integration
