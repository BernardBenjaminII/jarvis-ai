# Genesis VI-B0A — Projection Compatibility Certification

**Status:** Implemented  
**Parent:** Genesis VI-B0 — Executive Projection Plane

## Purpose

Preserve the canonical typed Projection Plane while restoring the historical
dictionary contract consumed by Genesis UI-A2.

## API separation

### Canonical typed API

```python
service.projection_envelopes() -> tuple[ProjectionEnvelope, ...]
service.executive_projection() -> ExecutiveProjection
```

### Historical compatibility API

```python
service.all_projections() -> dict
```

The compatibility response contains:

```text
generated_at
provider_count
overall_status
summary
projections
warnings
errors
metadata
```

`summary` contains a count for every `ProjectionStatus` value:

```text
available
degraded
unavailable
not_configured
unknown
```

## Invariants

1. `ProjectionRegistry` is unchanged.
2. `ProjectionEnvelope` is unchanged.
3. `ExecutiveProjection` is unchanged.
4. Canonical envelopes are created before compatibility serialization.
5. `all_projections()` does not introduce a second projection model.
6. Provider ordering remains deterministic.
7. UI-A2's `provider_count` and `summary` contract is certified.
8. Bootstrap, Operations routes, and the FastAPI application remain importable.

## Certification

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
./dev/verify_genesis_vi_b0a.sh
```

Full parent certification:

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
./dev/verify_genesis_vi_b0.sh
```
