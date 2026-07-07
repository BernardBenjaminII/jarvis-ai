# ADR-0007 — Knowledge Lifecycle

**Status:** Accepted

**Date:** 2026-07-03

**Owner:** JARVIS Knowledge Engine

---

# Context

ADR-0006 established that the fundamental unit of knowledge within JARVIS is the **Knowledge Object**.

With the introduction of the Knowledge Registry, JARVIS now requires a formal lifecycle describing how every Knowledge Object progresses from initial discovery to long-term maintenance.

Without a defined lifecycle:

- processing stages become inconsistent
- duplicate work increases
- validation becomes unreliable
- knowledge provenance is lost
- incremental updates become difficult

A formal lifecycle establishes predictable transitions and allows every subsystem to understand the operational state of every Knowledge Object.

---

# Decision

Every Knowledge Object SHALL progress through a defined lifecycle managed by the Knowledge Registry.

The Knowledge Registry SHALL be the authoritative operational record for every Knowledge Object.

The Library Catalog SHALL remain responsible only for descriptive metadata.

---

# Architectural Separation

JARVIS distinguishes between descriptive knowledge and operational state.

```
Filesystem
      │
      ▼
Discovery
      │
      ▼
Knowledge Object Builder
      │
      ▼
Knowledge Registry
      │
      ├──────────────┐
      ▼              ▼
Library Catalog   Assimilation Queue
      │              │
      └──────┬───────┘
             ▼
      Knowledge Graph
```

The Registry manages lifecycle.

The Catalog describes content.

The two systems SHALL remain independent.

---

# Knowledge Lifecycle

Every Knowledge Object SHALL progress through the following stages.

```
Discovered
      │
      ▼
Classified
      │
      ▼
Knowledge Object Built
      │
      ▼
Registered
      │
      ▼
Validated
      │
      ▼
Queued
      │
      ▼
Extracted
      │
      ▼
Chunked
      │
      ▼
Embedded
      │
      ▼
Knowledge Graph Integrated
      │
      ▼
Available
      │
      ▼
Deprecated
      │
      ▼
Archived
```

No stage may bypass an earlier stage.

---

# Lifecycle States


> **Legacy ADR**
>
> This ADR was created before the JARVIS ADR governance policy was established.
>
> Duplicate ADR numbers from this era are preserved intentionally for historical continuity.
>
> Beginning with **ADR-0017**, all Architecture Decision Records use unique,
> immutable numbering.

## Discovered

The filesystem has identified candidate material.

Responsible subsystem:

- discovery

---

## Classified

The material has been classified according to the ontology.

Responsible subsystem:

- classification

---

## Knowledge Object Built

Related files have been grouped into a coherent Knowledge Object.

Responsible subsystem:

- objects

---

## Registered

The Knowledge Object has been assigned an operational record.

Responsible subsystem:

- registry

---

## Validated

The object has passed structural validation.

Examples include:

- required metadata exists
- object is complete
- no critical corruption
- relationships are valid

Responsible subsystem:

- validation

---

## Queued

The object has been scheduled for assimilation.

Responsible subsystem:

- queue

---

## Extracted

Content has been extracted from source documents.

Responsible subsystem:

- extraction

---

## Chunked

Semantic chunks have been generated.

Responsible subsystem:

- chunking

---

## Embedded

Vector embeddings have been created.

Responsible subsystem:

- embeddings

---

## Knowledge Graph Integrated

Relationships have been incorporated into the Knowledge Graph.

Responsible subsystem:

- graph

---

## Available

The Knowledge Object is available for reasoning, retrieval, and memory.

Responsible subsystem:

- search
- retrieval
- memory

---

## Deprecated

The object remains available but has been superseded.

Examples:

- newer edition
- improved source
- duplicate with higher confidence

---

## Archived

The object is retained for provenance but excluded from active reasoning.

---

# Registry Responsibilities

The Knowledge Registry SHALL maintain operational state for every Knowledge Object.

Required attributes include:

- UUID
- lifecycle state
- validation state
- assimilation state
- trust level
- source
- duplicate relationships
- operational notes
- timestamps

The Registry SHALL NOT duplicate descriptive metadata maintained by the Library Catalog.

---

# Library Catalog Responsibilities

The Library Catalog SHALL maintain descriptive metadata including:

- title
- author
- publisher
- edition
- ISBN
- language
- subject
- keywords
- page count

The Catalog SHALL NOT manage operational lifecycle.

---

# State Transition Rules

Knowledge Objects SHALL only advance through valid transitions.

Example:

```
Discovered
    ↓
Classified
    ↓
Knowledge Object Built
```

Valid.

```
Discovered
    ↓
Queued
```

Invalid.

Similarly:

```
Registered
    ↓
Embedded
```

is invalid because extraction and chunking have not occurred.

---

# Operational Principles

## Single Source of Truth

The Knowledge Registry SHALL be the authoritative source for lifecycle state.

---

## Immutable Provenance

Every transition SHALL preserve:

- timestamp
- originating subsystem
- previous state

Future implementations may maintain a complete transition history.

---

## Incremental Processing

Only Knowledge Objects requiring processing SHALL advance.

Previously completed stages SHALL NOT be repeated unless explicitly invalidated.

---

## Failure Isolation

Failure of one Knowledge Object SHALL NOT interrupt processing of unrelated Knowledge Objects.

Objects may remain in an intermediate lifecycle state until corrected.

---

## Explainability

JARVIS SHALL be able to explain:

- current lifecycle state
- previous state
- reason for transition
- subsystem responsible

---

# Relationship to ADR-0006

ADR-0006 defines:

> What knowledge is.

ADR-0007 defines:

> How knowledge moves through the system.

Both ADRs are complementary.

---

# Consequences

## Benefits

- deterministic processing
- repeatable assimilation
- incremental updates
- complete provenance
- operational transparency
- easier debugging
- scalable processing
- future distributed synchronization

## Trade-offs

- additional operational metadata
- lifecycle management complexity
- stricter state transition rules

These costs are accepted because they significantly improve reliability and maintainability.

---

# Guiding Principle

> **Knowledge is not assimilated when it is discovered.**
>
> **Knowledge is assimilated only after it has completed its lifecycle up to the appropriate stage.**
>
> The Knowledge Registry exists to ensure every Knowledge Object progresses through that lifecycle in a deterministic, explainable, and repeatable manner.
