# ADR-0039 — Observation Migration Strategy

**Status:** Accepted  
**Phase:** Genesis IV-B4

## Context

Genesis IV-B3 discovered three non-canonical classes named `Observation`.
Repository analysis proved that they represent different semantic roles rather
than three interchangeable versions of one object.

## Decision

Adopt compatibility-before-removal.

1. `core/observation/contracts.py` remains the sole constitutional owner.
2. The cognition-common contract is approved legacy with an adapter.
3. The operational model is deprecated toward `ObservationRecord`.
4. The representation model is deprecated toward `RepresentedStatement`.
5. Every legacy conversion crosses an explicit compatibility boundary.
6. Unknown Observation definitions remain forbidden.
7. Renames and consumer rewrites occur in Genesis IV-B5.

## Consequences

The repository can certify governance without pretending that migration is
finished. Legacy usage remains visible, measurable, and removable.
