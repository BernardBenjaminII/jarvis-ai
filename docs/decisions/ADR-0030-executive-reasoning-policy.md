# ADR-0030 — Executive Reasoning Policy

**Status:** Accepted  
**Date:** 2026-07-24  
**Decision owner:** Genesis IV-A5

## Context

Evidence assessment alone does not determine whether JARVIS should select a
hypothesis. A reasoner must compare alternatives while preserving uncertainty
and refusing unjustified certainty.

## Decision

JARVIS shall establish `core.cognition.reasoner` as the canonical owner of
hypothesis comparison and executive judgment.

Selection shall be governed by an immutable `ReasoningPolicy` defining:

- minimum selection score;
- minimum confidence;
- minimum evidence coverage;
- minimum winning margin;
- maximum tolerated contradiction.

The reasoner shall expose explicit abstention dispositions:

- deferred;
- inconclusive;
- contested.

It shall never silently select the highest-ranked hypothesis when policy is not
satisfied.

## Consequences

Executive judgments become deterministic, auditable, and reproducible.

Future decision synthesis may consume a reasoning result without reimplementing
hypothesis comparison or uncertainty handling.
