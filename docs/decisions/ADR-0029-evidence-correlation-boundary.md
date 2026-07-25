# ADR-0029 — Evidence Correlation Boundary

**Status:** Accepted  
**Date:** 2026-07-24  
**Decision owner:** Genesis IV-A4

## Context

JARVIS already contains a canonical evidence domain under `core.evidence`.

Executive cognition nevertheless requires a dedicated mechanism for evaluating
how evidence bears on IV-A3 hypotheses.

Creating another generic `core.cognition.evidence` package would duplicate
ownership and risk semantic divergence.

## Decision

JARVIS shall establish `core.cognition.evidence_correlation` as the cognition
layer responsible for linking situation observations to hypotheses.

The layer shall:

- consume IV-A2 situations and IV-A3 hypotheses;
- preserve evidence polarity;
- separate support from contradiction;
- account for strength, reliability, and admissibility;
- expose coverage and missing-evidence questions;
- create deterministic immutable assessments;
- avoid redefining the canonical `core.evidence` contracts.

## Consequences

The architecture preserves one evidence domain while adding an explicit
cognitive evaluation boundary.

Future integration may adapt canonical `core.evidence` records into
`EvidenceLink` inputs without changing IV-A4 assessment semantics.
