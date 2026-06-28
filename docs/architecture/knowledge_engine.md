# JARVIS Knowledge Engine Architecture

**Status:** Draft  
**Version:** 0.1  
**Owner:** JARVIS Core  
**Purpose:** Define the architecture for JARVIS knowledge ingestion, storage, indexing, retrieval, and access.

---

## 1. Purpose

The Knowledge Engine is responsible for ingesting, organizing, indexing, retrieving, and maintaining all knowledge available to JARVIS regardless of source.

It is not just a RAG pipeline.

RAG is one capability of the Knowledge Engine. The larger goal is to create a persistent, cross-platform knowledge subsystem that can support:

- JARVIS
- DoomsdayDisk
- AI Knowledge Assistant concepts
- Personal documents
- Project documentation
- Source code
- Manuals
- Offline reference libraries

---

## 2. Core Principle

Repository contains behavior.

Runtime contains state.

The repository stores code, interfaces, architecture, and configuration.

The runtime stores knowledge data, indexes, embeddings, catalogs, logs, manifests, and generated artifacts.

---

## 3. Runtime Layout

Knowledge data lives under the runtime partition:

```text
JARVIS_RUNTIME/
└── knowledge/
    ├── catalog.sqlite
    ├── providers.sqlite
    ├── taxonomy.sqlite
    ├── cache/
    ├── chunks/
    ├── embeddings/
    ├── indexes/
    ├── manifests/
    └── thumbnails/
