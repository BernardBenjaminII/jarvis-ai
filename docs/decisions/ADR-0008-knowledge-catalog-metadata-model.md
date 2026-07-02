# ADR-0008: Knowledge Catalog and Metadata Model

## Status

Accepted

## Date

2026-07-01

## Context

JARVIS now has a structured `Knowledge/` repository and a Librarian subsystem capable of inventory, verification, duplicate detection, and gap analysis.

However, filesystem paths alone are not enough. JARVIS needs a formal catalog that understands documents, sources, topics, provenance, trust, quality, verification, editions, and relationships.

## Decision

JARVIS will introduce a first-class Knowledge Catalog.

The Knowledge Catalog will be the authoritative metadata layer for all known knowledge assets. It will track files, documents, sources, topics, provenance, verification state, quality scores, trust scores, and future ingestion status.

## Core Principle

JARVIS will distinguish between:

- A **file**: a physical object on disk.
- A **document**: an intellectual work.
- A **source**: where the document came from.
- A **topic**: what the document is about.
- A **relationship**: how documents relate to one another.

## Initial Catalog Capabilities

The catalog will support:

- Document registration
- File registration
- Topic taxonomy
- Source registry
- Verification metadata
- Trust and quality scoring
- Gap analysis support
- Duplicate awareness
- Future ingestion and embedding tracking

## Database

The catalog will use SQLite initially.

Default location:

```text
/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite
