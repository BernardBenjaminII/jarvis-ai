# ADR-0010: Canonical Knowledge Objects

## Status

Accepted

## Date

2026-07-02

## Decision

JARVIS will represent knowledge as Canonical Knowledge Objects, or CKOs.

A CKO is the intellectual unit of knowledge. Files are representations of that object.

Example:

- CKO: MIT 18.06 Lecture 01 - The Geometry of Linear Equations
- Representations:
  - PDF
  - HTML
  - JSON metadata
  - Markdown extraction
  - Plain text extraction
  - Future embeddings

## Why

PDFs are valuable because they preserve original formatting, diagrams, equations, and source fidelity.

Markdown/text are valuable because they are easier to search, chunk, embed, and reason over.

JARVIS will keep both without duplicating the underlying knowledge.

## Initial Implementation

The first implementation will target MIT OCW course ZIPs.

It will:

1. Scan extracted MIT OCW course packages.
2. Read resource folders.
3. Identify related files.
4. Create one CKO per resource.
5. Attach PDF, HTML, JSON, and future Markdown as representations.
6. Write a SQLite CKO catalog.
7. Produce a human-readable manifest.

## Non-Goals

This ADR does not implement full semantic duplicate detection, OCR, embeddings, or RAG.
