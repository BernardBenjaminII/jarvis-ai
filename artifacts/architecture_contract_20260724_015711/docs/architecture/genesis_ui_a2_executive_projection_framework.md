# Genesis UI-A2 — Executive Projection Framework

## Objective

Create the canonical read-model integration plane that converts domain subsystem state into stable, transparent, versioned projections for FastAPI and Mission Control.

## Contract

Every provider declares `projection_id`, `schema_version`, `health()`, and `project()`.
Every envelope includes provider identity, generation time, source time when known, health, data, warnings, and errors.

## Rules

1. Providers are read-only adapters.
2. Unknown state is never converted to zero.
3. Partial failure produces `degraded`.
4. Domain services remain authoritative.
5. FastAPI consumes the integration service rather than internal databases.
6. New subsystem providers are additive.

## Capability configuration

```bash
export JARVIS_CAPABILITY_PACKAGES="package.one,package.two"
```

An empty configuration reports `not_configured` instead of fabricated success.
