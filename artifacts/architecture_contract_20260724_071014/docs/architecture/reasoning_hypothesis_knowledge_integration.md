# Phase X-B — Hypothesis Generation and Knowledge Evidence Integration

## Purpose

Phase X-B connects Knowledge Engine retrieval output to the deterministic
Reasoning Engine and introduces bounded competing-hypothesis generation.

## Pipeline

```text
Knowledge search callable
        |
        v
raw search or ranking results
        |
        v
KnowledgeEvidenceAdapter
        |
        +-- source and chunk provenance
        +-- retrieval/ranking score
        +-- quality score
        +-- ranking explanation
        +-- stable evidence identity
        |
        v
EvidenceItem[]
        |
        v
DeterministicHypothesisGenerator
        |
        +-- evidence-backed synthesis
        +-- competing insufficiency hypothesis
        +-- optional conflict hypothesis
        |
        v
ReasoningEngine
        |
        v
PlanningRecommendation
```

## Supported result contracts

Production search objects may expose:

- `score`
- `file_path`
- `chunk_index`
- `text`
- `quality`

Ranked mappings may expose:

- `ranking_score`
- `source`
- `chunk_index`
- `text`
- `quality`
- `ranking`

The adapter accepts attribute-based and mapping-based forms.

## Translation policy

Retrieval relevance becomes evidence confidence. Content quality becomes
evidence reliability. Source path and chunk index remain explicit provenance.
The adapter does not claim that relevance proves truth.

## Generation policy

The generator does not invent domain facts. It creates only bounded
hypotheses concerning whether the available evidence supports the stated goal,
is insufficient, or contains unresolved conflict.

## Dependency boundary

The pipeline receives an injected callable:

```python
search(query: str, limit: int) -> Iterable[result]
```

It does not construct the Knowledge database or import the Knowledge Director.
That keeps reasoning independent of runtime wiring.

## Safety boundary

Phase X-B does not execute tools, mutate knowledge, authorize a plan, create a
runtime mission, autonomously expand research, or call an LLM.

## Next phase

Phase X-C should extract explicit claims from retrieved text, relate evidence
to claims, and detect agreement or conflict across sources before hypothesis
assessment.
