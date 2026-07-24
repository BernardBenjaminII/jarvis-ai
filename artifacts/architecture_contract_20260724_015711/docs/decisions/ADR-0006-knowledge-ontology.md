# ADR-0006 — Knowledge Ontology

**Status:** Accepted

**Date:** 2026-07-03

**Owner:** JARVIS Knowledge Engine

---

# Context

The original Knowledge Engine treated individual files as the fundamental unit of knowledge.

Testing against a real-world knowledge library (~90,000 discovered files) demonstrated that this assumption is fundamentally incorrect.

Knowledge is not stored as isolated files.

Knowledge exists as coherent entities composed of many files, directories, metadata, media, and supporting resources.

Examples include:

- Books
- Git repositories
- University projects
- Documentation sets
- Website archives
- Courses
- Datasets
- Manuals

Treating every file as an independent knowledge unit results in:

- fragmented understanding
- duplicate processing
- poor classification
- broken relationships
- inefficient embeddings
- weak semantic retrieval

Therefore the Knowledge Engine requires a formal ontology defining the hierarchy of knowledge.

---

# Decision

The primary unit of knowledge inside JARVIS SHALL be the **Knowledge Object**.

Files SHALL be considered storage artifacts rather than first-class knowledge entities.

All stages of the Knowledge Acquisition Pipeline SHALL operate on Knowledge Objects whenever possible.

---

# Knowledge Hierarchy

```
Library
│
├── Collection
│      │
│      ├── Knowledge Object
│      │       │
│      │       ├── Component
│      │       │       │
│      │       │       ├── Document
│      │       │       │       │
│      │       │       │       ├── Chunk
│      │       │       │       │
│      │       │       │       └── Embedding
│      │       │       │
│      │       │       └── Media
│      │       │
│      │       └── Metadata
│      │
│      └── Relationships
│
└── Memory
```

---

# Ontology Definitions


> **Legacy ADR**
>
> This ADR was created before the JARVIS ADR governance policy was established.
>
> Duplicate ADR numbers from this era are preserved intentionally for historical continuity.
>
> Beginning with **ADR-0017**, all Architecture Decision Records use unique,
> immutable numbering.

## Library

A Library represents every body of knowledge available to JARVIS.

Examples include:

- Local SSD
- NAS
- External Drives
- Cloud Storage
- Future User Libraries

A Library contains Collections.

---

## Collection

Collections are organizational containers.

Collections organize knowledge but are not knowledge themselves.

Examples:

- Programming
- Cybersecurity
- Aviation
- Religion
- Languages
- History
- University
- Military

Collections may contain other Collections.

---

## Knowledge Object

A Knowledge Object is the smallest independently meaningful entity that a human would naturally recognize.

Examples:

- Effective C (Second Edition)
- Linux Kernel Programming
- Benjamin Project 3
- CMSC430 Compiler Project
- FAA UH-60 Maintenance Manual
- The Quran
- Afghanistan War Diary

Knowledge Objects are the fundamental unit of knowledge inside JARVIS.

Everything ultimately references a Knowledge Object.

---

## Component

Components are logical subdivisions of a Knowledge Object.

Examples:

Book

- Chapters
- Appendices
- Exercises

Repository

- Source Code
- Documentation
- Tests
- Examples

Website

- Articles
- Images
- CSS
- JavaScript

Components exist only within Knowledge Objects.

---

## Document

Documents are individual files containing information.

Examples:

- PDF
- EPUB
- DOCX
- HTML
- Markdown
- TXT
- ZIM

Documents belong to Components or directly to Knowledge Objects.

Documents never belong directly to the Library.

---

## Chunk

Chunks are semantic subdivisions created during extraction.

Chunks exist solely to improve retrieval.

Chunks are implementation artifacts.

Chunks are **not** knowledge.

---

## Embedding

Embeddings are vector representations of Chunks.

Embeddings are retrieval mechanisms.

Embeddings are never the authoritative representation of knowledge.

---

# Knowledge Object Metadata

Every Knowledge Object SHALL contain:

- UUID
- Title
- Knowledge Type
- Subject
- Domain
- Language
- Author
- Version
- Source
- License
- Acquisition Date
- Confidence
- Assimilation Status
- Fingerprint
- Tags
- Relationships
- Last Modified Timestamp

Additional metadata may be added in future versions.

---

# Initial Knowledge Types

The ontology SHALL initially support:

- Book
- Repository
- Academic Project
- Course
- Manual
- Documentation
- Dataset
- Reference
- Research Paper
- Presentation
- Notebook
- Website Archive
- Image Collection
- Audio Collection
- Video Collection
- Conversation
- Unknown

Knowledge Types SHALL be extensible.

---

# Knowledge Acquisition Pipeline

Knowledge SHALL progress through the following stages.

```
Discovery
        │
        ▼
Knowledge Object Builder
        │
        ▼
Knowledge Registry
        │
        ▼
Classification
        │
        ▼
Deduplication
        │
        ▼
Validation
        │
        ▼
Assimilation Queue
        │
        ▼
Extraction
        │
        ▼
Chunking
        │
        ▼
Embeddings
        │
        ▼
Knowledge Graph
        │
        ▼
Memory
```

No stage may bypass an earlier stage.

---

# Relationships

Knowledge Objects may contain typed relationships.

Examples include:

- contains
- part_of
- references
- extends
- depends_on
- translated_from
- derived_from
- duplicates
- cites
- successor
- predecessor
- implements

Relationships SHALL exist primarily between Knowledge Objects.

---

# Source of Truth

The authoritative hierarchy SHALL be:

```
Knowledge Object
        │
        ▼
Document
        │
        ▼
Chunk
        │
        ▼
Embedding
```

Embeddings SHALL NEVER replace source material.

Original content SHALL always remain authoritative.

---

# Assimilation Policy

A Knowledge Object SHALL NOT be assimilated until it has completed:

- Discovery
- Knowledge Object Construction
- Classification
- Validation

Only validated Knowledge Objects may enter the Assimilation Queue.

---

# Architectural Principles

## Human First

The ontology shall be understandable by humans before machines.

---

## Knowledge Before Files

Knowledge Objects represent ideas.

Files merely store them.

---

## Explainability

JARVIS shall always be able to explain:

- why a Knowledge Object exists
- where it originated
- how it was classified
- how it entered the system

---

## Reversible

No pipeline stage shall destroy original source material.

All transformations shall be reproducible.

---

## Incremental

Knowledge acquisition shall be repeatable without generating duplicates.

Only new or modified Knowledge Objects should require processing.

---

## Immutable Provenance

Every Knowledge Object shall permanently preserve:

- origin
- acquisition history
- transformations
- classification history
- assimilation history

---

## Vendor Independence

The ontology defines concepts—not implementation.

It SHALL remain independent of:

- SQLite
- PostgreSQL
- FAISS
- Chroma
- Qdrant
- Ollama
- OpenAI
- any specific vector database
- any specific LLM

---

# Consequences

## Benefits

- Stable long-term architecture
- Reduced duplication
- Better semantic retrieval
- Meaningful knowledge relationships
- Cleaner embeddings
- Easier incremental updates
- Easier multi-user support
- Supports distributed JARVIS instances
- Scales to millions of Knowledge Objects

## Trade-offs

- Additional metadata management
- Slightly more complex acquisition pipeline
- Greater initial design effort

These trade-offs are accepted because they significantly improve long-term maintainability and scalability.

---

# Future Extensions

This ontology is expected to support future capabilities including:

- Multi-user libraries
- Federated Knowledge Registries
- Distributed JARVIS deployments
- Autonomous knowledge acquisition
- Automatic relationship discovery
- Confidence scoring
- Knowledge aging and freshness
- Knowledge quality metrics
- Knowledge lineage visualization

---

# Guiding Principle

> **JARVIS does not learn files.**
>
> **JARVIS learns Knowledge Objects.**
>
> Files are merely one method of storing knowledge.
>
> The mission of the Knowledge Engine is to transform storage artifacts into coherent, explainable, interconnected Knowledge Objects that become part of JARVIS's understanding of the world.
