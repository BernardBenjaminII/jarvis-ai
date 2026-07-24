# AB-0011: Knowledge Mapping Layer

## Status

Draft

## Purpose

The Knowledge Mapping Layer connects acquired knowledge with the Knowledge Coverage Graph.

Acquisition pipelines understand files.

The Knowledge Graph understands concepts.

The Mapping Layer translates between them.

## Responsibilities

- classify incoming material
- assign ontology subjects
- assign ontology concepts
- map CKOs to ontology nodes
- preserve provenance
- expose confidence scores

## Inputs

- Canonical Knowledge Objects
- Librarian Catalog
- Source metadata
- Acquisition metadata
- File paths
- Extracted text

## Outputs

- mapped subjects
- mapped concepts
- confidence
- provenance

## Principle

The Knowledge Graph should never infer knowledge directly from filenames.

All conceptual placement must occur through the Knowledge Mapping Layer.
