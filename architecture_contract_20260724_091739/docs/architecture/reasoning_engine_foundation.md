# JARVIS Reasoning Engine Foundation

## Status

Phase X — Implemented foundation.

## Purpose

The Reasoning Engine determines what conclusions are justified by explicit
evidence and converts the selected conclusion into a structured recommendation
that the Planning Engine can later consume.

It does not execute actions and it does not create runtime missions.

## Canonical pipeline

```text
Knowledge and observations
          |
          v
ReasoningRequest
          |
          v
ReasoningEngine
          |
          +-- validates evidence references
          +-- scores support and contradiction
          +-- accounts for assumptions
          +-- ranks hypotheses deterministically
          +-- records missing information
          +-- records contradictions
          +-- emits a justification trace
          |
          v
ReasoningResult
          |
          +-- selected hypothesis
          +-- confidence and disposition
          +-- planning recommendation
          +-- deterministic fingerprint
```

## Phase X contract

Inputs:

- a goal;
- explicit evidence;
- candidate hypotheses;
- assumptions;
- constraints;
- context.

Outputs:

- an assessment for every hypothesis;
- a selected conclusion when justified;
- unresolved information;
- contradictions;
- an immutable reasoning trace;
- a structured planning recommendation;
- a deterministic result fingerprint.

## Confidence model

Each evidence item has:

```text
weight = reliability * confidence
```

For each hypothesis:

```text
support_score = sum(supporting evidence weights)
contradiction_score = sum(contradicting evidence weights)
uncertainty = number_of_assumptions * 0.25

confidence =
    support_score
    / (support_score + contradiction_score + uncertainty)
```

This formula is intentionally simple, inspectable, and replaceable. It is a
constitutional baseline, not a claim that every domain can be reduced to one
universal probability model.

## Dispositions

- `supported`: support exists and confidence is at least 0.67;
- `tentative`: support exists but confidence is below 0.67;
- `insufficient`: no supporting evidence exists;
- `rejected`: contradiction outweighs support.

## Determinism

The same `ReasoningRequest` produces the same:

- hypothesis ordering;
- scores;
- selected conclusion;
- planning recommendation;
- trace;
- fingerprint.

The foundation generates no timestamps and makes no network or model calls.

## Boundaries

Phase X does not:

- retrieve knowledge autonomously;
- invoke an LLM;
- mutate the Knowledge Engine;
- create a canonical planning `Mission`;
- compile a plan;
- execute tools;
- approve actions;
- alter the Executive runtime.

These integrations belong to later controlled phases.

## Next phase

Phase X-B should add a Knowledge Evidence Adapter that converts ranked
Knowledge Engine retrieval results into `EvidenceItem` contracts while
preserving source identity, provenance, retrieval score, and trust state.
