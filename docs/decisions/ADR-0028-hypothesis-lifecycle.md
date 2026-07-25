# ADR-0028 — Executive Hypothesis Lifecycle

**Status:** Accepted  
**Date:** 2026-07-24  
**Decision owner:** Genesis IV-A3

## Context

The situation model describes what is known, but executive cognition also
requires explicit candidate explanations.

Embedding possible explanations directly inside a situation would blur facts
and interpretation.

## Decision

JARVIS shall establish `core.cognition.hypothesis` as the canonical owner of
candidate explanatory propositions.

Hypotheses shall:

- remain separate from observations and situations;
- preserve source-situation identity;
- use deterministic semantic identifiers;
- support multiple competing candidates;
- identify supporting and contradicting observations;
- expose assumptions and unresolved questions;
- begin in `PROPOSED` status;
- avoid claiming confirmation before evidence evaluation.

## Consequences

Later evidence correlation can compare hypotheses without altering the source
observations or situation snapshot.

The architecture gains a clear boundary between representation and inference.
