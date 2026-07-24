# Genesis VI-A3B — Compatibility Finalization

## Purpose

Genesis VI-A3B restores the public route contract introduced by Genesis UI-A2
without replacing or weakening the Genesis VI-A3 Executive Projection Bus.

## Compatibility surface

The Operations boundary exposes both API generations:

- `/operations/projections`
- `/operations/projections/{projection_id}`
- `/operations/capabilities`
- `/operations/capabilities/{capability_name}`
- `/operations/bridge`
- `/operations/bridge/readiness`
- `/operations/bridge/manifest`
- `/operations/bridge/projections/{projection_id}`

## Ownership

The Executive Integration runtime remains the canonical owner of projections
and capability metadata. Compatibility endpoints delegate to that runtime and
do not maintain independent registries or duplicate projection logic.

The Executive Projection Bus remains the canonical normalized readiness and
bridge surface.

## Failure behavior

Unknown projection and capability identifiers return HTTP 404 responses.

## Certification

Certification requires UI-A2, UI-A3, UI-A4.1, VI-A2, and VI-A3 regressions to
pass together.
