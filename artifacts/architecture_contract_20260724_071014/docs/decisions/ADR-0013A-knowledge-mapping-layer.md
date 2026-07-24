# ADR-0013A: Knowledge Mapping Layer

## Status

Accepted

## Context

The first implementation of the Gap Analysis Engine compared ontology subjects directly against filenames.

This approach is insufficient because:

- different sources organize knowledge differently
- filenames rarely describe concepts
- folders may use different terminology
- CKOs already contain richer metadata

## Decision

Introduce a Knowledge Mapping Layer.

The Mapping Layer becomes the only subsystem responsible for assigning ontology locations to acquired knowledge.

Gap Analysis consumes mapped concepts rather than filenames.

## Consequences

Future coverage measurements become independent of filesystem layout.

The same ontology can support PDFs, HTML, Markdown, ZIM, APIs, journals, Git repositories, and future acquisition methods.
