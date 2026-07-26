# Genesis VI-B0 — Executive Projection Plane

**Status:** Implemented  
**Authority:** Genesis VI  
**Supersedes:** First VI-B0 Integration Contract Convergence installer

## Mission

Complete the partially implemented Executive Projection Plane as one coherent
runtime architecture.

## Canonical flow

```text
Runtime Services
      │
      ├── OperationsProjectionProvider
      ├── CapabilityProjectionProvider
      └── KnowledgeProjectionProvider
                   │
                   ▼
           ProjectionEnvelope
                   │
                   ▼
           ProjectionRegistry
                   │
                   ▼
      ExecutiveProjectionService
                   │
                   ▼
          ExecutiveProjection
                   │
          ┌────────┴────────┐
          ▼                 ▼
     Operations API    Mission Control UI
```

## Canonical ownership

- `core.integration.contracts`
  - `ProjectionStatus`
  - `ProjectionHealth`
  - `ProjectionEnvelope`
  - `ExecutiveProjection`

- `core.integration.registry`
  - `CapabilityRegistry`
  - `ProjectionRegistry`

- `core.integration.service`
  - `ExecutiveProjectionService`
  - `ExecutiveIntegrationService` compatibility service

## Governing rules

1. Every provider has a unique non-empty `projection_id`.
2. Every provider implements `project()`.
3. Every provider returns `ProjectionEnvelope`.
4. Provider failures become unavailable envelopes unless strict execution is requested.
5. Projection order is deterministic by `projection_id`.
6. Aggregate executive health reflects the most severe provider state.
7. Provider and aggregate timestamps are timezone-aware UTC datetimes.
8. Envelope `data` and `metadata` mappings are immutable.
9. `ProjectionStatus.UNKNOWN` is valid for indeterminate service state.
10. The legacy repository-analysis service remains available during migration.
11. The package public API is exported through `core.integration`.
12. Certification must cross the bootstrap, Operations route, and FastAPI import boundaries.

## Certification

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
./dev/verify_genesis_vi_b0.sh
```

After certification:

```bash
./run_jarvis.sh
```
