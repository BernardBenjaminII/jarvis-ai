# ADR-0015 — Semantic Extraction Engine

## Status

Accepted

---

# Context

JARVIS has successfully implemented:

- Knowledge Acquisition Pipeline
- Knowledge Catalog
- Knowledge Graph
- Coverage Graph
- Gap Analysis
- Trusted Source Discovery
- Semantic Registration
- Collection Discovery
- Document Inspection

These systems allow JARVIS to:

- know where knowledge exists
- know what has been downloaded
- know which collections exist
- know what subjects are missing

However, JARVIS still primarily categorizes documents using:

- folder location
- filename
- manually written keyword rules

These approaches are insufficient.

A document may contain hundreds of concepts that never appear in its filename.

Examples:

Emergency War Surgery.pdf

contains:

- hemorrhage
- trauma
- airway
- burns
- vascular surgery
- orthopedic trauma
- blast injury
- shock

None of these appear in the filename.

Likewise,

MIT Linear Algebra

contains

- eigenvalues
- determinants
- vector spaces
- orthogonality
- singular value decomposition

without those necessarily appearing in the file name.

Therefore filename classification has reached its architectural limit.

JARVIS must begin understanding document contents.

---

# Decision

Introduce the Semantic Extraction Engine.

The Semantic Extraction Engine becomes the primary intelligence layer responsible for transforming raw documents into structured knowledge.

Instead of assigning knowledge from filenames, JARVIS will derive knowledge from document contents.

---

# Responsibilities

The Semantic Extraction Engine shall:

• inspect every document

• select the proper reader

• extract readable text

• detect language

• extract metadata

• extract title

• extract authors

• extract publication year

• extract headings

• extract table of contents

• extract glossary

• extract index

• extract repeated terminology

• extract named entities

• extract concepts

• extract keywords

• extract semantic relationships

• generate document summary

• assign confidence scores

• produce structured semantic metadata

---

# Inputs

PDF

HTML

Markdown

Plain text

EPUB

ZIM

DOCX

Future:

Audio

Video transcripts

Images (OCR)

Scanned books

---

# Outputs

Every document shall produce a semantic record.

Example

{
    "primary_subject": "electronics",

    "secondary_subjects": [
        "circuits",
        "analog electronics"
    ],

    "concepts": [
        "resistor",
        "capacitor",
        "transistor",
        "voltage",
        "current"
    ],

    "entities": [
        "Ohm's Law",
        "Kirchhoff",
        "BJT"
    ],

    "keywords": [...],

    "summary": "...",

    "confidence": 0.94
}

---

# Pipeline

Download

↓

Normalize

↓

Inspect

↓

Reader Selection

↓

Text Extraction

↓

Semantic Extraction

↓

Knowledge Catalog

↓

Knowledge Graph

↓

Gap Analysis

↓

Research Planner

↓

Question Answering

---

# Extraction Stages

Stage 1

Document Inspection

Determine true file type.

Never trust file extensions.

---

Stage 2

Reader Selection

Choose appropriate parser.

PDF

HTML

EPUB

ZIM

TXT

Future readers remain pluggable.

---

Stage 3

Structural Extraction

Extract:

title

headings

chapters

TOC

index

glossary

captions

tables

references

---

Stage 4

Semantic Extraction

Extract:

keywords

concepts

entities

topics

relationships

subject

difficulty

confidence

---

Stage 5

Summarization

Generate concise knowledge summary.

Not an LLM rewrite.

A factual representation of document contents.

---

Stage 6

Catalog Registration

Store

Subjects

Concepts

Keywords

Entities

Summary

Confidence

Relationships

Source metadata

---

# Design Principles

The Semantic Engine never modifies documents.

Extraction is repeatable.

Extraction is deterministic whenever possible.

LLMs enhance extraction.

LLMs do not replace deterministic extraction.

Every semantic result records confidence.

Every semantic result records provenance.

Every semantic result remains reproducible.

---

# Knowledge Philosophy

JARVIS does not collect files.

JARVIS collects knowledge.

Documents are merely containers.

Knowledge exists inside documents.

The Semantic Extraction Engine converts containers into structured knowledge.

---

# Future Extensions

Concept graph generation

Cross-document linking

Automatic duplicate detection

Citation graph

Contradiction detection

Document quality scoring

Knowledge aging

Authority scoring

Version comparison

Automatic ontology expansion

Knowledge compression

Knowledge synthesis

---

# Consequences

Advantages

Far more accurate categorization

Reduced manual keyword rules

Improved search

Improved gap analysis

Improved question answering

Better acquisition planning

Supports every future reader

Supports future LLM reasoning

Supports autonomous research

Tradeoffs

Longer ingestion time

Higher storage requirements

More metadata

Additional extractors required

More processing stages

These costs are acceptable because semantic understanding becomes the foundation of every higher-level JARVIS capability.

---

# Architecture Blueprint

The Semantic Extraction Engine becomes the central intelligence layer of the Knowledge Architecture.

Knowledge Library

↓

Document Inspector

↓

Reader Selection

↓

Structural Extraction

↓

Semantic Extraction Engine

↓

Knowledge Catalog

↓

Knowledge Graph

↓

Coverage Graph

↓

Gap Analysis

↓

Research Planner

↓

Acquisition Pipeline

↓

Question Answering

↓

Long-Term Memory

This ADR establishes semantic understanding—not file storage—as the primary architectural objective of the JARVIS knowledge system.
