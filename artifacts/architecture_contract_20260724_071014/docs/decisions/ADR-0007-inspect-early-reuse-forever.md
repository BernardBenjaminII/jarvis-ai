# ADR-0007 — Inspect Early, Reuse Forever

**Status:** Accepted

**Date:** 2026-07-05

---

# Context

Traditional Retrieval-Augmented Generation (RAG) systems largely treat documents as
collections of text.

Typical ingestion pipelines are:

Filesystem
→ Parse
→ Chunk
→ Embed
→ Search

Metadata extraction is often minimal and many systems repeatedly rediscover the same
information during search, retrieval, summarization, or agent execution.

JARVIS is intended to become a long-lived knowledge operating system rather than a
document search engine.

As the knowledge library grows into millions of resources, repeatedly analyzing the
same documents becomes computationally expensive and architecturally inefficient.

---

# Decision

JARVIS adopts the principle:

> Every resource should be understood once during ingestion and never need to be
> rediscovered.

Resource understanding occurs before chunking.

The ingestion pipeline becomes:

Filesystem

↓

Discovery

↓

Resource Detection

↓

Resource Inspection

↓

Knowledge Object

↓

Librarian / Catalog

↓

Extraction

↓

Chunking

↓

Embeddings

↓

Vector Index

↓

Knowledge Graph

↓

Specialists

↓

Headmaster

---

# Resource Detection

Resource Detection answers one question:

"What is this resource?"

Examples:

• Book

• Website Archive

• Codebase

• Academic Course

• Research Paper

• Dataset

• Video

• Audio Collection

• Image Collection

• Git Repository

• Project

This creates a canonical Knowledge Object.

---

# Resource Inspection

After identifying the resource type, a specialized inspector extracts every useful
piece of metadata practical for that resource.

Inspection is intentionally expensive.

It happens once.

Results are permanently stored.

---

# Example — Book Inspector

The Book Inspector may extract:

• Title

• Subtitle

• Authors

• Editors

• Publisher

• Edition

• Publication Year

• ISBN

• DOI

• Language

• Page Count

• Table of Contents

• Chapters

• Bibliography

• References

• Glossary

• Index

• Figures

• Tables

• Code Listings

• Exercises

• OCR Confidence

• Fingerprints

• Duplicate Candidates

• Structural Outline

---

# Example — Website Inspector

Website Inspector may extract:

• Website Title

• Homepage

• Site Description

• Language

• Generator

• Mirror Type

• Number of Pages

• Navigation Tree

• Internal Links

• External Links

• Sitemap

• Images

• PDFs

• Videos

• Metadata

• Last Modified

• Robots

• CSS Framework

• JavaScript Framework

---

# Example — Codebase Inspector

Codebase Inspector may extract:

• Programming Languages

• Frameworks

• Build System

• Package Manager

• Repository Type

• README

• License

• Dependencies

• Tests

• Documentation

• Architecture

• Modules

• Classes

• Functions

• APIs

• Build Instructions

---

# Example — Video Inspector

Video Inspector may extract:

• Codec

• Resolution

• Duration

• Chapters

• Subtitle Tracks

• Transcript

• OCR

• Scene Boundaries

• Speakers

• Topics

---

# Example — Course Inspector

Course Inspector may extract:

• Course Name

• Instructor

• Lessons

• Assignments

• Projects

• Exams

• Learning Objectives

• Skills

• Difficulty

• Prerequisites

---

# Benefits


> **Legacy ADR**
>
> This ADR was created before the JARVIS ADR governance policy was established.
>
> Duplicate ADR numbers from this era are preserved intentionally for historical continuity.
>
> Beginning with **ADR-0017**, all Architecture Decision Records use unique,
> immutable numbering.

## Single Source of Truth

Metadata is computed once.

Every subsystem consumes identical information.

---

## Performance

Expensive inspection is never repeated.

Search, retrieval, specialists, and summaries reuse stored metadata.

---

## Better Cataloging

The Librarian catalogs resources instead of files.

Examples:

Book

Website

Course

Dataset

Codebase

instead of

PDF

HTML

TXT

---

## Better Search

Search can combine:

Semantic vectors

+

Metadata

+

Knowledge graph

+

Relationships

rather than embeddings alone.

---

## Better Specialists

Specialists receive structured resources instead of raw chunks.

Programming Specialist receives:

Book

↓

Author

↓

Language

↓

Modules

↓

Examples

↓

Exercises

instead of anonymous text.

---

## Better Knowledge Graph

Relationships become first-class objects.

Book

↓

Author

↓

Topic

↓

Concept

↓

Prerequisite

↓

Course

↓

Project

↓

Dataset

---

## Scalability

The cost of inspection is paid once.

As the library grows into millions of resources, ingestion remains linear while
retrieval remains fast.

---

# Architectural Principle

JARVIS should think in terms of resources, not files.

Files are implementation details.

Resources are knowledge.

---

# Consequences

All future ingestion modules should implement:

1. Resource Detection

2. Resource Inspection

3. Structured Metadata Storage

before chunking occurs.

Chunking, embeddings, vector indexes, knowledge graphs, and specialist agents consume
this structured understanding rather than rediscovering it.

---

# Future Work

Resource inspectors will become a plugin architecture.

knowledge_engine/

resources/

    inspectors/

        book.py

        website.py

        codebase.py

        course.py

        dataset.py

        archive.py

        video.py

        audio.py

        images.py

        project.py

Each inspector owns its own extraction logic.

The ingestion pipeline remains open for future resource types without requiring
modification of downstream systems.

---

# Summary

JARVIS does not ingest files.

JARVIS discovers resources.

JARVIS understands resources.

JARVIS catalogs resources.

Everything else builds on that understanding.

