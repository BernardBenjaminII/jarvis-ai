# Genesis IV-B4 — Observation Migration & Compatibility

## Mission

Move the Executive Operating System toward the constitutional
`core.observation.Observation` contract without breaking established cognition,
runtime-observation, or representation subsystems.

## Governed Contracts

### Legacy cognition fact

`core/cognition/common/contracts.py`

This is an earlier deterministic fact contract. IV-B4 supplies a canonical
adapter and permits it as approved legacy until its consumers are migrated.

### Operational observation record

`core/cognition/observation/models.py`

This object represents a runtime event or record. It contains severity,
mission, correlation, causation, occurrence, and recording data. Its ultimate
semantic name is `ObservationRecord`.

### Represented statement

`core/representation/contracts.py`

This object represents an internal cognitive statement with bounded
confidence. Its ultimate semantic name is `RepresentedStatement`.

## Compatibility Rule

Compatibility exists at an explicit boundary. Legacy callers must identify
their originating contract. The boundary emits a deprecation warning and
returns a canonical Observation plus a migration receipt.

## Non-Goals

IV-B4 does not yet rename the operational or representation classes and does
not remove the legacy cognition contract. Those destructive changes belong to
Genesis IV-B5 after consumer migration is measured.

## Exit Criteria

- Every discovered non-canonical Observation has a migration-registry entry.
- Every registered definition has a canonical adapter or completed removal.
- No ungoverned Observation definitions remain.
- Adapter output is deterministic.
- Migration reports are reproducible.
