# ADR-0013: Gap Analysis Engine

## Status

Accepted

## Date

2026-07-02

## Context

JARVIS now has a Knowledge Coverage Graph ontology containing domains, disciplines, subjects, concepts, prerequisites, and campaigns.

The next step is to compare that ontology against the actual knowledge JARVIS currently has.

JARVIS should not merely count files. It should identify which areas of knowledge are strong, weak, missing, or blocked by weak prerequisites.

## Decision

JARVIS will include a Gap Analysis Engine.

The Gap Analysis Engine compares:

- the Knowledge Coverage Graph
- the filesystem Knowledge library
- known CKOs
- known campaigns
- known concepts
- prerequisite rules

and produces a coverage report.

## Initial Implementation

The first implementation will compare ontology subjects against matching folders and files in:

```text
/media/abdullah/JARVISDATA/Knowledge
