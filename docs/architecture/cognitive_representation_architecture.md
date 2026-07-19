# Cognitive Representation Architecture

**Status:** Phase X-C1 Foundation  
**Purpose:** Transform information artifacts into explicit, provenance-preserving structures suitable for deterministic reasoning.

## Governing principle

> The quality of reasoning is bounded by the quality of representation.

JARVIS must not treat arbitrary retrieval chunks as if they were already valid reasoning objects.

## Architectural position

```text
Knowledge Retrieval
        │
        ▼
Cognitive Representation
        │
        ▼
Reasoning
        │
        ▼
Planning
        │
        ▼
Mission Compilation
```

## Layered cognitive objects

“All of the above” is the governing answer, but the objects are layers rather than peers.

```text
Information Artifact
        │
        ▼
Structural Segment
        │
        ▼
Sentence or Record
        │
        ▼
Atomic Proposition
        │
        ├── Observation
        ├── Event
        ├── Definition
        ├── Rule
        └── Assertion
        │
        ▼
Entities and Relations
        │
        ▼
Claim
        │
        ▼
Hypothesis
        │
        ▼
Situation Model
        │
        ▼
Conclusion
        │
        ▼
Decision
```

No layer replaces the previous layer. Each enriches it and preserves provenance.

## Phase X-C1 scope

Phase X-C1 establishes:

- artifact references;
- immutable semantic segments;
- deterministic identifiers;
- exact source spans;
- headings, sentences, bullets, code blocks, table rows, and key-value records;
- subsystem isolation.

It does not yet infer propositions, entities, relations, truth, claims, or hypotheses.

## Chunking versus segmentation

Knowledge chunking serves storage, embedding, retrieval, and context-window management.

Cognitive segmentation serves meaning, provenance, articulation, and reasoning precision.

## Invariants

Given identical artifact identity, source text, and segmentation version, the result must be identical.

Every derived cognitive object must retain an unbroken provenance chain to its source artifact.

## Roadmap

- X-C1: Representation foundation and segmentation
- X-C2: Proposition articulation
- X-C3: Observation, event, definition, rule, and assertion typing
- X-C4: Entity and relation representation
- X-C5: Claim formation
- X-C6: Claim graph construction
- X-C7: Reasoning integration
