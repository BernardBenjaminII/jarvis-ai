# Genesis IV-A2 — Executive Situation Model

**Status:** Implemented  
**Depends on:** Genesis IV-A1  
**Canonical namespace:** `core.cognition.situation`

## Purpose

Genesis IV-A2 transforms immutable observations into coherent executive
situations.

A situation is not a new observation and is not yet a hypothesis. It is an
auditable representation of what is currently known, how observations relate,
and which mission or cognitive cycle they belong to.

```text
IV-A1 Observations
        |
        v
Executive Situation Projector
        |
        v
Situation Snapshot
        |
        +--> observation set
        +--> explicit relations
        +--> derived confidence
        +--> highest severity
        +--> mission/correlation context
        +--> deterministic identity
```

## Observation graph semantics

IV-A2 introduces explicit `SituationRelation` objects. They provide the first
observation-graph capability without inventing causal conclusions.

Relations may express correlation, temporal order, support, contradiction,
causation, or duplication. They are only included when explicitly supplied.

## Deterministic projection

Situation identity is derived from:

- title;
- sorted observation identifiers;
- sorted explicit relations;
- mission identifier;
- correlation identifier.

Observation ordering therefore cannot change the situation identity.

## Derived executive properties

The projector derives:

- `opened_at`: earliest observation occurrence;
- `updated_at`: latest occurrence or recording timestamp;
- `confidence`: arithmetic mean of observation confidence;
- `severity`: highest observation severity;
- mission and correlation identifiers when all observations agree.

## Deferred work

IV-A2 does not:

- generate hypotheses;
- judge evidence admissibility;
- infer unsupported causal relations;
- select decisions;
- execute actions;
- persist to SQLite.

Those responsibilities remain forward phases.
