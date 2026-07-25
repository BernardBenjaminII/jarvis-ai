# Genesis IV-A4 — Executive Evidence Correlation Engine

**Status:** Implemented  
**Depends on:** Genesis IV-A2 and IV-A3  
**Canonical namespace:** `core.cognition.evidence_correlation`

## Purpose

Genesis IV-A4 evaluates how explicit observation evidence bears on a candidate
hypothesis.

It does not redefine the canonical `core.evidence` domain. Instead, it provides
the cognition-layer correlation boundary that connects situation observations
to IV-A3 hypotheses.

```text
Situation Observations
        |
        v
Explicit Evidence Links
        |
        v
Executive Evidence Correlator
        |
        +--> support score
        +--> contradiction score
        +--> net score
        +--> coverage
        +--> confidence
        +--> missing evidence
```

## Correlation rules

Each evidence link identifies:

- one observation;
- one hypothesis;
- polarity;
- strength;
- reliability;
- admissibility;
- optional rationale.

Only admissible links contribute to scoring.

The engine never invents links. Callers must supply every claimed relationship.

## Assessment semantics

A hypothesis assessment contains independent support and contradiction scores.
This prevents contradictory evidence from disappearing into a single opaque
number.

Coverage measures the proportion of situation observations represented by
admissible, non-neutral links.

Confidence combines:

- the originating hypothesis confidence;
- assessment coverage;
- mean admissible-link reliability.

## Deferred work

IV-A4 does not:

- determine source authority policies;
- replace the canonical evidence domain;
- choose a winning hypothesis;
- perform executive reasoning;
- synthesize decisions;
- execute actions.
