# Genesis IV-A5 — Executive Reasoner

**Status:** Implemented  
**Depends on:** Genesis IV-A2, IV-A3, and IV-A4  
**Canonical namespace:** `core.cognition.reasoner`

## Purpose

Genesis IV-A5 transforms assessed competing hypotheses into a justified
executive judgment.

```text
Situation
   |
   +--> Hypotheses
   |       |
   |       +--> Evidence Assessments
   |                    |
   v                    v
          Executive Reasoner
                   |
                   +--> ranked hypotheses
                   +--> selected / deferred / inconclusive / contested
                   +--> confidence and margin
                   +--> unresolved assumptions
                   +--> evidence requests
```

## Constitutional behavior

The reasoner is deterministic and policy-governed.

It may select a hypothesis only when:

- the leading score meets policy;
- confidence meets policy;
- evidence coverage meets policy;
- contradiction is below policy;
- the margin over alternatives meets policy.

Otherwise, the reasoner abstains through one of three non-selection
dispositions:

- `DEFERRED`;
- `INCONCLUSIVE`;
- `CONTESTED`.

## Ranking score

Each assessed hypothesis receives a reasoning score:

```text
net evidence score × evidence coverage × assessment confidence
```

The score remains bounded from -1.0 to 1.0.

## Safety boundary

IV-A5 produces judgments, not decisions or actions.

It does not:

- synthesize an executive decision;
- authorize an operation;
- execute a mission;
- modify source observations;
- alter hypotheses or assessments.
