# Genesis VI-B0 — Integration Contract Convergence

**Status:** Implemented  
**Authority:** Genesis VI  
**Scope:** Integration provider contracts, executive projections, API import boundary

## Purpose

Genesis VI-B0 converges two previously disconnected contract families:

1. generic provider projections used by Integration providers; and
2. strongly typed executive projections used by Mission Control.

The canonical provider boundary is now:

```text
Integration Provider
        │
        ▼
ProjectionHealth
        │
        ▼
ProjectionEnvelope
        │
        ▼
ExecutiveProjection
        │
        ├── Operations API
        ├── Mission Control
        └── Commander UI
```

## Canonical contracts

The following types are canonical and public:

- `ProjectionStatus`
- `ProjectionHealth`
- `ProjectionEnvelope`
- `ExecutiveProjection`

The existing executive-domain contracts remain canonical:

- `CapabilityProjection`
- `IntegrationHealthProjection`
- `CommanderBriefProjection`
- `MissionControlProjection`
- `ExecutiveTimelineNode`

## Architectural rules

1. Providers emit `ProjectionEnvelope`.
2. Provider availability is expressed through `ProjectionStatus`.
3. Provider health is expressed through `ProjectionHealth`.
4. Executive aggregation is expressed through `ExecutiveProjection`.
5. Executive-domain projections remain strongly typed.
6. Provider contracts and executive contracts may not be replaced by aliases.
7. All timestamps in provider envelopes must be timezone-aware.
8. Envelope data and metadata are immutable mappings.
9. `core.integration` is the stable public import surface.
10. Application startup must successfully cross the Integration bootstrap and Operations route boundaries.

## Compatibility

Genesis VI-B0 restores the public symbols expected by the provider layer without
removing the Mission Control contract family.  This is additive convergence,
not a destructive replacement.

## Certification

Run:

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
./dev/verify_genesis_vi_b0.sh
```

After certification, verify operational startup:

```bash
./run_jarvis.sh
```
