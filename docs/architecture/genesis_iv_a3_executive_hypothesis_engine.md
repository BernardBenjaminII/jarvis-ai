# Genesis IV-A3 — Executive Hypothesis Engine

**Status:** Implemented  
**Depends on:** Genesis IV-A2  
**Canonical namespace:** `core.cognition.hypothesis`

## Purpose

Genesis IV-A3 converts executive situations into explicit candidate
explanations.

A hypothesis is not a conclusion. It is a traceable proposition that may be
supported, weakened, rejected, or confirmed by later evidence phases.

```text
Executive Situation
        |
        v
Hypothesis Proposals
        |
        v
Executive Hypothesis Generator
        |
        +--> Candidate A
        +--> Candidate B
        +--> Candidate C
```

## Guarantees

Each hypothesis contains:

- deterministic identity;
- source situation identity;
- statement and hypothesis kind;
- lifecycle status;
- provisional confidence;
- supporting observation references;
- contradicting observation references;
- assumptions;
- unresolved questions;
- rationale and labels.

## Safety boundary

IV-A3 does not infer certainty or select a winner. It preserves competing
hypotheses and rejects references to observations outside the source situation.

Evidence scoring, admissibility, ranking, and executive decision-making remain
future responsibilities.
